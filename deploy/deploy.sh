#!/usr/bin/env bash
# deploy.sh <staging|production> [options]
#
# Deploys the SCEPA upload stack (database-builder-scepa-rs) and Studio to one
# environment over SSH, then runs deploy_smoke_test.sh and writes a deployment
# record. Without --apply it is a read-only dry run: it prints exactly what
# would change and writes nothing.
#
# Options:
#   --apply              Perform the deployment (default is a dry run).
#   --upload-ref REF     Commit to deploy for the upload stack: a branch name or
#   --studio-ref REF     a commit SHA (7 to 40 hex characters). Default: this
#                        environment's branch (current-staging or
#                        current-production). Use a SHA to roll back.
#   --reload-caddy       Reload Caddy even when its config is unchanged. A
#                        changed config is always installed and reloaded.
#   --no-smoke           Skip deploy_smoke_test.sh after deploying.
#   --yes                Skip the confirmation prompt for production.
#   -h, --help           Show this help.
#
# Environment:
#   SCEPA_SSH_USER       SSH login name on the VMs (default: ssh's own default).
#   SCEPA_DEPLOY_RECORDS Directory for deployment records
#                        (default: ./deployment-records).
#
# Needs locally: bash, ssh, gh (logged in), jq, git, curl. The VM needs
# passwordless sudo. Deployment records contain host, version and commit data
# but no secrets; keep them out of the repository.
#
# Exit status: 0 success, 1 blocked or failed, 2 bad usage.

# sed indents every line of a multi-line value, which ${var//x/y} cannot do.
# shellcheck disable=SC2001
set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=environments.sh
source "$SCRIPT_DIR/environments.sh"

die() { echo "error: $*" >&2; exit 1; }
usage() { sed -n '2,/^$/p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//' | sed '$d'; }

APPLY=0
ASSUME_YES=0
RELOAD_CADDY=0
RUN_SMOKE=1
UPLOAD_REF=""
STUDIO_REF=""
ENV_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --yes) ASSUME_YES=1 ;;
    --reload-caddy) RELOAD_CADDY=1 ;;
    --no-smoke) RUN_SMOKE=0 ;;
    --upload-ref) [[ $# -ge 2 ]] || { usage >&2; exit 2; }; UPLOAD_REF=$2; shift ;;
    --studio-ref) [[ $# -ge 2 ]] || { usage >&2; exit 2; }; STUDIO_REF=$2; shift ;;
    -h | --help) usage; exit 0 ;;
    -*) echo "error: unknown option $1" >&2; usage >&2; exit 2 ;;
    *) [[ -z "$ENV_ARG" ]] || { echo "error: more than one environment given" >&2; exit 2; }; ENV_ARG=$1 ;;
  esac
  shift
done
[[ -n "$ENV_ARG" ]] || { usage >&2; exit 2; }
load_environment "$ENV_ARG" || exit 2

for tool in ssh gh jq git curl; do
  command -v "$tool" >/dev/null 2>&1 || die "'$tool' is required but not installed"
done

RECORDS_DIR=${SCEPA_DEPLOY_RECORDS:-$PWD/deployment-records}
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)
STARTED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
STARTED_LOCAL=$(date +%Y-%m-%dT%H:%M:%S%z)
OPERATOR_LOCAL="$(id -un)@$(hostname -s)"
SCRIPT_COMMIT=$(git -C "$SCRIPT_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)
if [[ -n "$(git -C "$SCRIPT_DIR" status --porcelain -- "$SCRIPT_DIR" 2>/dev/null)" ]]; then
  SCRIPT_COMMIT="$SCRIPT_COMMIT (with uncommitted changes in deploy/)"
fi
TEMPLATE="$SCRIPT_DIR/templates/Caddyfile.$ENV_NAME"
CADDY_TMP="/tmp/scepa-caddyfile-$RUN_ID"
WORK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/scepa-deploy.XXXXXX")

APPLY_STARTED=0
RECORD_WRITTEN=0
RESULT=""
RESULT_DETAIL=""

cleanup() {
  local status=$?
  if [[ $APPLY_STARTED -eq 1 && $RECORD_WRITTEN -eq 0 ]]; then
    [[ -n "$RESULT" ]] || { RESULT=FAILED; RESULT_DETAIL="interrupted or crashed before the run finished"; }
    write_record
  fi
  remote "rm -f '$CADDY_TMP'" </dev/null >/dev/null 2>&1 || true
  close_ssh
  rm -rf "$WORK_DIR"
  exit "$status"
}
trap cleanup EXIT

[[ -f "$TEMPLATE" ]] || die "missing Caddyfile template $TEMPLATE"
open_ssh || die "cannot reach $HOST over SSH (set SCEPA_SSH_USER if your login name differs)"
REMOTE_USER=$(remote id -un </dev/null 2>/dev/null)

# ---- Remote scripts (kept outside $( ... ) so bash 3.2 can parse them) --------

read -r -d '' LIVE_SCRIPT <<'LIVE_EOF'
for d in "$@"; do
  o=$(stat -c %U "$d")
  g() { sudo -u "$o" git -C "$d" "$@"; }
  printf '%s|%s|%s|%s|%s|%s\n' "$d" "$o" "$(g rev-parse --abbrev-ref HEAD)" "$(g rev-parse HEAD)" \
    "$(g status --porcelain --untracked-files=no | wc -l | tr -d ' ')" "$(g log -1 --format=%s)"
done
LIVE_EOF

read -r -d '' PREFLIGHT_SCRIPT <<'PRE_EOF'
set -u
EXPECT_ENV=$1; HOST=$2; UP=$3; ST=$4; UP_CHANGES=$5
out() { printf '%s|%s\n' "$1" "$2"; }
env_of() { grep -m1 "^$2=" "$1" 2>/dev/null | cut -d= -f2- | tr -d '"'; }

if systemctl is-active --quiet docker; then out OK "docker is active"; else out BLOCK "docker is not active"; fi
if systemctl is-active --quiet caddy; then out OK "caddy is active"; else out BLOCK "caddy is not active"; fi

root=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null)
free_gb=$(df --output=avail -BG "${root:-/}" | tail -1 | tr -dc '0-9')
if [ "${free_gb:-0}" -lt 10 ]; then out BLOCK "only ${free_gb:-0} GiB free under ${root:-/}; image builds need about 10"
else out OK "${free_gb} GiB free under $root"; fi

for f in "$UP/.env" "$ST/.env" "$ST/backend/mcp_tools.local.json"; do
  if [ -f "$f" ]; then out OK "$f exists"; else out BLOCK "$f is missing"; fi
done

v=$(env_of "$ST/.env" LANGFUSE_TRACING_ENVIRONMENT)
if [ "$v" = "$EXPECT_ENV" ]; then out OK "studio .env sets LANGFUSE_TRACING_ENVIRONMENT=$v"
else out BLOCK "studio .env must contain LANGFUSE_TRACING_ENVIRONMENT=$EXPECT_ENV (found '${v:-nothing}'). Add it before deploying."; fi
v=$(env_of "$ST/.env" OAUTH_REDIRECT_URI)
if [ "$v" = "https://$HOST/chatep/api/auth/callback" ]; then out OK "studio .env OAUTH_REDIRECT_URI matches this host"
else out BLOCK "studio .env OAUTH_REDIRECT_URI is '${v:-nothing}', not this host's callback (wrong environment's file?)"; fi
v=$(env_of "$ST/.env" FRONTEND_ORIGIN)
if [ "$v" = "https://$HOST" ]; then out OK "studio .env FRONTEND_ORIGIN matches this host"
else out BLOCK "studio .env FRONTEND_ORIGIN is '${v:-nothing}', expected https://$HOST"; fi

if [ "$UP_CHANGES" = 1 ]; then
  n=$(curl -s --max-time 20 http://127.0.0.1:9070/query -H 'accept: application/json' -H 'content-type: application/json' \
    -d "{\"query\":\"select count(*) as n from sys_invocation where status <> 'completed'\"}" | jq -r '.rows[0].n // empty' 2>/dev/null)
  if [ -z "$n" ]; then out BLOCK "cannot read Restate's in-flight invocations; workflow code changes need them drained"
  elif [ "$n" -gt 0 ]; then out BLOCK "$n Restate invocations are still in flight; drain them before changing workflow code"
  else out OK "no Restate invocations in flight"; fi
fi
PRE_EOF

read -r -d '' CADDY_SCRIPT <<'CADDY_EOF'
tpl=$1; live=/etc/caddy/Caddyfile
a=$(caddy adapt --config "$live" --adapter caddyfile 2>/dev/null | jq -S .)
b=$(caddy adapt --config "$tpl" --adapter caddyfile 2>/dev/null | jq -S .)
if [ -z "$a" ] || [ -z "$b" ]; then echo "ERROR|could not adapt one of the Caddyfiles"; exit 0; fi
if [ "$a" = "$b" ]; then echo "SAME|"; else
  echo "DIFFERENT|"
  diff -u <(caddy fmt "$live" 2>/dev/null) <(caddy fmt "$tpl" 2>/dev/null) | tail -n +3
fi
CADDY_EOF

read -r -d '' APPLY_SCRIPT <<'APPLY_EOF'
set -euo pipefail
UP_DIR=$1; UP_SHA=$2; UP_KIND=$3; UP_REF=$4
ST_DIR=$5; ST_SHA=$6; ST_KIND=$7; ST_REF=$8
CADDY_ACTION=$9; CADDY_TMP=${10}; RUN_ID=${11}

exec 9>/run/lock/scepa-deploy.lock
flock -n 9 || { echo "ERROR: another deployment holds /run/lock/scepa-deploy.lock"; exit 75; }
step() { printf '\n== %s\n' "$*"; }

update_repo() { # dir sha kind ref
  local dir=$1 sha=$2 kind=$3 ref=$4 owner
  owner=$(stat -c %U "$dir")
  g() { sudo -u "$owner" git -C "$dir" "$@"; }
  step "git $dir -> $sha ($kind $ref), as $owner"
  if [ "$kind" = branch ]; then
    g fetch --quiet origin "+refs/heads/$ref:refs/remotes/origin/$ref"
    [ "$(g rev-parse "origin/$ref")" = "$sha" ] || { echo "ERROR: origin/$ref moved since the plan was made; re-run"; exit 1; }
    if g show-ref --verify --quiet "refs/heads/$ref"; then g checkout --quiet "$ref"; else g checkout --quiet -b "$ref" "origin/$ref"; fi
    g merge --ff-only --quiet "$sha"
  else
    g fetch --quiet origin "$sha"
    g checkout --quiet --detach "$sha"
  fi
  [ "$(g rev-parse HEAD)" = "$sha" ] || { echo "ERROR: HEAD is not $sha after checkout"; exit 1; }
  echo "HEAD is now $(g rev-parse --short HEAD) on $(g rev-parse --abbrev-ref HEAD)"
}

deploy_stack() { # dir
  step "compose $1"
  cd "$1"
  docker compose -f compose.release.yaml config --quiet </dev/null
  docker compose -f compose.release.yaml up -d --build --wait --wait-timeout 900 </dev/null
  docker compose -f compose.release.yaml ps --format 'table {{.Service}}\t{{.Status}}' </dev/null
}

update_repo "$UP_DIR" "$UP_SHA" "$UP_KIND" "$UP_REF"
deploy_stack "$UP_DIR"
update_repo "$ST_DIR" "$ST_SHA" "$ST_KIND" "$ST_REF"
deploy_stack "$ST_DIR"

if [ "$CADDY_ACTION" != none ]; then
  step "caddy ($CADDY_ACTION)"
  if [ "$CADDY_ACTION" = install ]; then
    caddy validate --config "$CADDY_TMP" >/dev/null 2>&1 || { echo "ERROR: new Caddyfile does not validate; live config untouched"; exit 1; }
    cp -p /etc/caddy/Caddyfile "/etc/caddy/Caddyfile.bak-$RUN_ID"
    echo "previous Caddyfile saved as /etc/caddy/Caddyfile.bak-$RUN_ID"
    cat "$CADDY_TMP" > /etc/caddy/Caddyfile
  fi
  caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1 || { echo "ERROR: live Caddyfile does not validate"; exit 1; }
  systemctl reload caddy
  echo "caddy reloaded, state: $(systemctl is-active caddy)"
fi
step "done"
APPLY_EOF

read -r -d '' READY_SCRIPT <<'READY_EOF'
for i in $(seq 1 60); do
  ok=1
  for u in http://127.0.0.1:8002/health http://127.0.0.1:3000/openapi.json http://127.0.0.1:5173/upload/ \
           http://127.0.0.1:10090/chatep/ http://127.0.0.1:10092/api/docs; do
    [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$u")" = 200 ] || { ok=0; break; }
  done
  if [ "$ok" = 1 ]; then echo "all local endpoints answered after about $(( (i - 1) * 2 )) seconds"; exit 0; fi
  sleep 2
done
echo "WARNING: local endpoints were still not all answering after 120 seconds"
exit 1
READY_EOF

read -r -d '' INVENTORY_SCRIPT <<'INV_EOF'
set -u
UP=$1; ST=$2
row() { printf '| %s | %s |\n' "$1" "$2"; }
ver() { dpkg-query -W -f='${Version}' "$1" 2>/dev/null || echo "not installed"; }
cand() { apt-cache policy "$1" 2>/dev/null | awk '/Candidate:/ {print $2}'; }
head2() { echo; echo "### $1"; echo; echo "| $2 | $3 |"; echo "|---|---|"; }
PKGS="docker-ce docker-ce-cli docker-ce-rootless-extras docker-compose-plugin docker-buildx-plugin containerd.io caddy git openssh-server fail2ban ufw unattended-upgrades jq curl"

. /etc/os-release
head2 "Operating system" Item Value
row "Host" "$(hostname -f)"
row "OS" "$PRETTY_NAME"
row "Kernel" "$(uname -r)"
row "CPUs / memory" "$(nproc) / $(free -h | awk '/Mem:/ {print $2}')"
row "Booted" "$(uptime -s)"

head2 "Packages (dpkg)" Package Installed
for p in $PKGS; do row "$p" "$(ver "$p")"; done

head2 "Runtime versions (reported by the programs)" Component Version
row "Docker Engine (server)" "$(docker version --format '{{.Server.Version}} (API {{.Server.APIVersion}})' 2>/dev/null)"
row "Docker CLI (client)" "$(docker version --format '{{.Client.Version}}' 2>/dev/null)"
row "Docker Compose" "$(docker compose version --short 2>/dev/null)"
row "Docker Buildx" "$(docker buildx version 2>/dev/null | awk '{print $2}')"
row "containerd" "$(containerd --version 2>/dev/null | awk '{print $3}')"
row "runc" "$(runc --version 2>/dev/null | head -1 | awk '{print $3}')"
row "Caddy" "$(caddy version 2>/dev/null | awk '{print $1}')"
row "Git" "$(git --version | awk '{print $3}')"

head2 "Docker configuration" Item Value
row "Docker root dir" "$(docker info --format '{{.DockerRootDir}}' 2>/dev/null)"
row "Storage driver" "$(docker info --format '{{.Driver}}' 2>/dev/null)"
row "Cgroup driver" "$(docker info --format '{{.CgroupDriver}}' 2>/dev/null)"
row "Default runtime" "$(docker info --format '{{.DefaultRuntime}}' 2>/dev/null)"
row "/etc/docker/daemon.json" "$(tr -d '\n\t ' < /etc/docker/daemon.json 2>/dev/null || echo none)"
row "containerd root" "$(grep -E '^root' /etc/containerd/config.toml 2>/dev/null | tr -d ' ' || echo default)"
row "Caddy systemd override" "$(tr '\n' ';' < /etc/systemd/system/caddy.service.d/override.conf 2>/dev/null || echo none)"

head2 "Versions inside the containers (what the image tags resolved to)" Component Version
cexec() { docker exec "$@" </dev/null 2>/dev/null | head -1; }
qk=$(grep -m1 '^QDRANT_API_KEY=' "$UP/.env" 2>/dev/null | cut -d= -f2-)
row "PostgreSQL (SCEPA)" "$(cexec upload-interface-postgres-1 postgres --version | awk '{print $3}')"
row "PostgreSQL (Studio)" "$(cexec studio-studio_postgres-1 postgres --version | awk '{print $3}')"
row "Redis" "$(cexec studio-redis-1 redis-server --version | awk '{print $3}' | sed 's/^v=//')"
row "Qdrant" "$(printf 'header = "api-key: %s"\n' "$qk" | curl -s -K - --max-time 10 http://127.0.0.1:6333/ | jq -r '.version // empty' 2>/dev/null)"
row "TypeDB" "$(cexec upload-interface-typedb-1 /opt/typedb-server-linux-x86_64/typedb server --version | awk '{print $2}')"
row "Restate" "$(curl -s --max-time 10 http://127.0.0.1:9070/version | jq -r '.version // empty' 2>/dev/null)"
row "Garage" "$(cexec upload-interface-garage-1 /garage --version | awk '{print $2}')"
row "GROBID" "$(curl -s --max-time 10 http://127.0.0.1:8070/api/version | jq -r '.version // empty' 2>/dev/null)"

head2 "Container images" Container "Image / image id of the running container"
for n in $(docker ps -a --format '{{.Names}}' | sort); do
  info=$(docker inspect -f '{{.Config.Image}} {{.Image}}' "$n" 2>/dev/null)
  img=${info%% *}; id=${info##* }; id=${id#sha256:}
  row "$n" "$img / ${id:0:12}"
done

head2 "System services" Service "State / enabled at boot"
for s in docker containerd caddy fail2ban unattended-upgrades; do row "$s" "$(systemctl is-active "$s" 2>&1) / $(systemctl is-enabled "$s" 2>&1)"; done
row "ufw" "$(ufw status 2>/dev/null | head -1)"
row "Held apt packages" "$(apt-mark showhold | tr '\n' ' ')"

echo; echo "### Available updates (from the apt lists as last refreshed, not refreshed by this script)"; echo
echo "| Package | Installed | Candidate |"; echo "|---|---|---|"
for p in $PKGS; do printf '| %s | %s | %s |\n' "$p" "$(ver "$p")" "$(cand "$p")"; done

echo; echo "### Container status"; echo
echo "| Container | Status | Ports |"; echo "|---|---|---|"
docker ps -a --format '| {{.Names}} | {{.Status}} | {{.Ports}} |' | sort

echo; echo "### Docker volumes"; echo; echo '```text'; docker volume ls --format '{{.Name}}' | sort; echo '```'
echo; echo "### Compose projects"; echo; echo '```text'; docker compose ls 2>/dev/null; echo '```'

echo; echo "### Git checkouts"; echo
echo "| Path | Owner | Branch | Commit | Subject | Origin |"; echo "|---|---|---|---|---|---|"
for d in "$UP" "$ST"; do
  o=$(stat -c %U "$d"); g() { sudo -u "$o" git -C "$d" "$@"; }
  printf '| %s | %s | %s | %s | %s | %s |\n' "$d" "$o" "$(g rev-parse --abbrev-ref HEAD)" "$(g rev-parse HEAD)" "$(g log -1 --format=%s | tr '|' '/')" "$(g remote get-url origin)"
done

echo; echo "### Caddyfile (/etc/caddy/Caddyfile)"; echo
echo "sha256: $(sha256sum /etc/caddy/Caddyfile | cut -d' ' -f1)"; echo
echo '```caddy'; cat /etc/caddy/Caddyfile; echo '```'
INV_EOF

# ---- Helpers ------------------------------------------------------------------

BLOCKERS=""
WARNINGS=""
add_block() { BLOCKERS="${BLOCKERS}$1"$'\n'; }
add_warn() { WARNINGS="${WARNINGS}$1"$'\n'; }

resolve_ref() { # repo ref -> "sha|kind|ref"
  local repo=$1 ref=${2:-} sha
  [[ -n "$ref" ]] || ref=$TARGET_BRANCH
  if [[ "$ref" =~ ^[0-9a-fA-F]{7,40}$ ]]; then
    sha=$(gh api "repos/$repo/commits/$ref" --jq .sha 2>/dev/null) || die "commit $ref not found in $repo"
    echo "$sha|sha|$ref"
  elif [[ "$ref" =~ ^[A-Za-z0-9._/-]+$ ]]; then
    sha=$(git ls-remote "https://github.com/$repo.git" "refs/heads/$ref" | awk '{print $1}')
    [[ -n "$sha" ]] || die "branch $ref not found in $repo"
    echo "$sha|branch|$ref"
  else
    die "'$ref' is neither a branch name nor a commit SHA"
  fi
}

# compare_repo repo live target prefix: sets <prefix>_STATUS, _COMMITS, _FILES
compare_repo() {
  local repo=$1 live=$2 target=$3 prefix=$4 out status commits files
  if [[ "$live" == "$target" ]]; then
    printf -v "${prefix}_STATUS" '%s' identical
    printf -v "${prefix}_COMMITS" '%s' ""
    printf -v "${prefix}_FILES" '%s' ""
    return
  fi
  if ! out=$(gh api "repos/$repo/compare/$live...$target" 2>/dev/null); then
    printf -v "${prefix}_STATUS" '%s' unknown
    printf -v "${prefix}_COMMITS" '%s' ""
    printf -v "${prefix}_FILES" '%s' ""
    return
  fi
  status=$(jq -r '"\(.status) (ahead \(.ahead_by), behind \(.behind_by))"' <<<"$out")
  commits=$(jq -r '.commits[] | "- `\(.sha[0:7])` \(.commit.message | split("\n")[0])"' <<<"$out" | head -40)
  files=$(jq -r '.files[]? | "- \(.filename) (\(.status))"' <<<"$out" | head -60)
  printf -v "${prefix}_STATUS" '%s' "$status"
  printf -v "${prefix}_COMMITS" '%s' "$commits"
  printf -v "${prefix}_FILES" '%s' "$files"
}

live_state() { # sets UP_LIVE_*/ST_LIVE_* and *_DIRTY from the VM; returns 1 on failure
  local out dir branch sha dirty
  UP_LIVE_SHA=""; ST_LIVE_SHA=""
  out=$(remote "sudo bash -s -- '$UPLOAD_DIR' '$STUDIO_DIR'" <<<"$LIVE_SCRIPT") || { echo "error: could not read the live git state on $HOST" >&2; return 1; }
  while IFS='|' read -r dir _ branch sha dirty _; do
    if [[ "$dir" == "$UPLOAD_DIR" ]]; then
      UP_LIVE_BRANCH=$branch; UP_LIVE_SHA=$sha; UP_DIRTY=$dirty
    elif [[ "$dir" == "$STUDIO_DIR" ]]; then
      ST_LIVE_BRANCH=$branch; ST_LIVE_SHA=$sha; ST_DIRTY=$dirty
    fi
  done <<<"$out"
  [[ -n "$UP_LIVE_SHA" && -n "$ST_LIVE_SHA" ]] || { echo "error: could not parse the live git state: $out" >&2; return 1; }
}

inventory_markdown() { remote "sudo bash -s -- '$UPLOAD_DIR' '$STUDIO_DIR'" <<<"$INVENTORY_SCRIPT"; }

stable_sections() {
  awk '/^### /{keep = ($0 ~ /Packages|Runtime versions|Versions inside|Docker configuration|Container images|System services/)} keep' "$1"
}

repo_section() { # title repo dir live_branch live_sha req_kind req_ref target_sha after_sha rel commits files
  echo "### $1"
  echo
  echo "| Item | Value |"
  echo "|---|---|"
  echo "| Repository | https://github.com/$2 |"
  echo "| Path on VM | $3 |"
  echo "| Branch before | $4 |"
  echo "| Commit before | $5 |"
  echo "| Requested | $7 ($6) |"
  echo "| Target commit | $8 |"
  echo "| Commit after | $9 |"
  echo "| Target relative to live | ${10} |"
  if [[ -n "${11}" ]]; then
    echo
    echo "Commits deployed:"
    echo
    echo "${11}"
  fi
  if [[ -n "${12}" ]]; then
    echo
    echo "Files changed:"
    echo
    echo "${12}"
  fi
  echo
}

write_record() {
  local file finished_utc finished_local
  mkdir -p "$RECORDS_DIR"
  file="$RECORDS_DIR/$ENV_NAME-deploy-$RUN_ID.md"
  finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  finished_local=$(date +%Y-%m-%dT%H:%M:%S%z)
  {
    echo "# $ENV_NAME deployment record $RUN_ID"
    echo
    echo "- Result: **$RESULT**${RESULT_DETAIL:+, $RESULT_DETAIL}"
    echo "- Environment: $ENV_NAME ($HOST)"
    echo "- Started: $STARTED_UTC UTC ($STARTED_LOCAL local)"
    echo "- Finished: $finished_utc UTC ($finished_local local)"
    echo "- Operator: $OPERATOR_LOCAL, SSH login ${REMOTE_USER:-unknown} on the VM"
    echo "- Script: deploy.sh, studio repo commit $SCRIPT_COMMIT"
    echo "- Options: smoke test $([[ $RUN_SMOKE -eq 1 ]] && echo run || echo skipped), forced Caddy reload $([[ $RELOAD_CADDY -eq 1 ]] && echo yes || echo no)"
    echo
    echo "## Repositories"
    echo
    repo_section "Upload stack (database-builder-scepa-rs)" "$UPLOAD_REPO" "$UPLOAD_DIR" "$UP_BEFORE_BRANCH" "$UP_BEFORE_SHA" \
      "$UP_KIND" "$UP_REFNAME" "$UP_SHA" "${UP_AFTER_SHA:-not read}" "$UP_STATUS" "$UP_COMMITS" "$UP_FILES"
    repo_section "Studio (studio)" "$STUDIO_REPO" "$STUDIO_DIR" "$ST_BEFORE_BRANCH" "$ST_BEFORE_SHA" \
      "$ST_KIND" "$ST_REFNAME" "$ST_SHA" "${ST_AFTER_SHA:-not read}" "$ST_STATUS" "$ST_COMMITS" "$ST_FILES"
    echo "## Software versions and host configuration after the deployment"
    echo
    echo "Collected from the VM at the end of the run. Versions are what the programs report, with dpkg package versions alongside."
    if [[ -s "$WORK_DIR/inventory-after.md" ]]; then
      cat "$WORK_DIR/inventory-after.md"
    else
      echo
      echo "_Not collected: the VM could not be read at the end of the run._"
    fi
    echo
    echo "### Software version changes during this deployment"
    echo
    if [[ -s "$WORK_DIR/inventory-before.md" && -s "$WORK_DIR/inventory-after.md" ]]; then
      stable_sections "$WORK_DIR/inventory-before.md" >"$WORK_DIR/stable-before.txt"
      stable_sections "$WORK_DIR/inventory-after.md" >"$WORK_DIR/stable-after.txt"
      if diff -u "$WORK_DIR/stable-before.txt" "$WORK_DIR/stable-after.txt" >"$WORK_DIR/stable.diff"; then
        echo "None. Package, runtime, image and configuration versions are the same before and after."
      else
        echo '```diff'
        tail -n +3 "$WORK_DIR/stable.diff"
        echo '```'
      fi
    else
      echo "_Cannot compare: the before or after inventory is missing._"
    fi
    echo
    echo "## Caddy"
    echo
    echo "- Action: $CADDY_ACTION"
    if [[ "$CADDY_STATE" == DIFFERENT ]]; then
      echo
      echo '```diff'
      echo "$CADDY_DIFF"
      echo '```'
    fi
    echo
    echo "## Smoke test"
    echo
    if [[ -s "$WORK_DIR/smoke.txt" ]]; then
      echo '```text'
      cat "$WORK_DIR/smoke.txt"
      echo '```'
    else
      echo "_Not run._"
    fi
    echo
    echo "## Deployment log"
    echo
    if [[ -s "$WORK_DIR/apply.log" ]]; then
      echo '```text'
      cat "$WORK_DIR/apply.log"
      echo '```'
    else
      echo "_The deployment step did not run._"
    fi
    echo
    echo "## Rollback"
    echo
    echo "This restores the code that was running before, by commit. It does not undo data or schema changes in Postgres, TypeDB, Qdrant, Garage or Restate, nor edits to the \`.env\` files."
    echo
    echo '```bash'
    echo "deploy/deploy.sh $ENV_NAME --apply --upload-ref $UP_BEFORE_SHA --studio-ref $ST_BEFORE_SHA"
    echo '```'
    echo
    echo "The VM is left on a detached HEAD after a SHA deployment. The previous Caddyfile, if it was replaced, is on the VM as \`/etc/caddy/Caddyfile.bak-$RUN_ID\`."
  } >"$file"
  RECORD_WRITTEN=1
  echo
  echo "Deployment record: $file"
}

# ---- Plan ---------------------------------------------------------------------

echo "Environment: $ENV_NAME ($HOST), mode: $([[ $APPLY -eq 1 ]] && echo APPLY || echo "dry run")"
echo

IFS='|' read -r UP_SHA UP_KIND UP_REFNAME <<<"$(resolve_ref "$UPLOAD_REPO" "$UPLOAD_REF")" || exit 1
IFS='|' read -r ST_SHA ST_KIND ST_REFNAME <<<"$(resolve_ref "$STUDIO_REPO" "$STUDIO_REF")" || exit 1
[[ -n "$UP_SHA" && -n "$ST_SHA" ]] || exit 1

live_state || exit 1
UP_BEFORE_BRANCH=$UP_LIVE_BRANCH; UP_BEFORE_SHA=$UP_LIVE_SHA
ST_BEFORE_BRANCH=$ST_LIVE_BRANCH; ST_BEFORE_SHA=$ST_LIVE_SHA
compare_repo "$UPLOAD_REPO" "$UP_LIVE_SHA" "$UP_SHA" UP
compare_repo "$STUDIO_REPO" "$ST_LIVE_SHA" "$ST_SHA" ST

UP_CHANGES=0; [[ "$UP_LIVE_SHA" != "$UP_SHA" ]] && UP_CHANGES=1
ST_CHANGES=0; [[ "$ST_LIVE_SHA" != "$ST_SHA" ]] && ST_CHANGES=1

check_repo_rules() { # label kind status dirty
  local label=$1 kind=$2 status=$3 dirty=$4
  [[ "$dirty" -gt 0 ]] && add_block "$label checkout on the VM has $dirty modified tracked files; clean it first"
  case "$status" in
    unknown) add_block "$label: the live commit is not on GitHub, so the change cannot be checked (local commits on the VM?)" ;;
    behind* | diverged*)
      if [[ "$kind" == branch ]]; then
        add_block "$label: target branch is $status relative to the live commit. To go back deliberately, pass an explicit commit SHA."
      else
        add_warn "$label: the target commit is $status relative to the live commit (rollback or sideways deploy)"
      fi
      ;;
  esac
}
check_repo_rules "Upload stack" "$UP_KIND" "$UP_STATUS" "$UP_DIRTY"
check_repo_rules "Studio" "$ST_KIND" "$ST_STATUS" "$ST_DIRTY"

PRE_OUT=$(remote "sudo bash -s -- '$ENV_NAME' '$HOST' '$UPLOAD_DIR' '$STUDIO_DIR' '$UP_CHANGES'" <<<"$PREFLIGHT_SCRIPT") || add_block "preflight checks could not run on the VM"
PRE_OK=""
while IFS='|' read -r level msg; do
  case "$level" in
    BLOCK) add_block "$msg" ;;
    WARN) add_warn "$msg" ;;
    OK) PRE_OK="${PRE_OK}  ok    $msg"$'\n' ;;
  esac
done <<<"$PRE_OUT"

CADDY_STATE=ERROR
CADDY_DIFF=""
CADDY_OUT=""
if remote "umask 077; cat > '$CADDY_TMP'" <"$TEMPLATE"; then
  CADDY_OUT=$(remote "sudo bash -s -- '$CADDY_TMP'" <<<"$CADDY_SCRIPT")
  CADDY_STATE=${CADDY_OUT%%|*}
  CADDY_DIFF=$(printf '%s\n' "$CADDY_OUT" | tail -n +2)
fi
case "$CADDY_STATE" in
  SAME) if [[ $RELOAD_CADDY -eq 1 ]]; then CADDY_ACTION=reload; else CADDY_ACTION=none; fi ;;
  DIFFERENT) CADDY_ACTION=install ;;
  *) CADDY_ACTION=none; add_block "could not compare the Caddyfile with the template ($CADDY_OUT)" ;;
esac

echo "Plan"
echo "----"
printf '%-8s %-44s %s\n' "Stack" "Live" "Target"
printf '%-8s %-44s %s\n' "upload" "${UP_LIVE_SHA:0:7} on $UP_LIVE_BRANCH" "${UP_SHA:0:7} ($UP_KIND $UP_REFNAME)"
printf '%-8s %-44s %s\n' "studio" "${ST_LIVE_SHA:0:7} on $ST_LIVE_BRANCH" "${ST_SHA:0:7} ($ST_KIND $ST_REFNAME)"
echo
echo "upload: $UP_STATUS$([[ $UP_CHANGES -eq 0 ]] && echo ', no code change; compose will still run (a no-op when nothing differs)')"
[[ -n "$UP_COMMITS" ]] && echo "$UP_COMMITS" | sed 's/^/  /'
echo "studio: $ST_STATUS$([[ $ST_CHANGES -eq 0 ]] && echo ', no code change; compose will still run (a no-op when nothing differs)')"
[[ -n "$ST_COMMITS" ]] && echo "$ST_COMMITS" | sed 's/^/  /'
[[ -n "$ST_FILES" ]] && { echo "studio files changed:"; echo "$ST_FILES" | sed 's/^/  /'; }
[[ -n "$UP_FILES" ]] && { echo "upload files changed:"; echo "$UP_FILES" | sed 's/^/  /'; }
echo
echo "caddy:  $CADDY_STATE -> action: $CADDY_ACTION"
if [[ "$CADDY_STATE" == DIFFERENT ]]; then echo "$CADDY_DIFF" | sed 's/^/  /'; fi
echo
echo "Preflight"
printf '%s' "$PRE_OK"
if [[ -n "$WARNINGS" ]]; then printf '%s' "$WARNINGS" | sed 's/^/  warn  /'; fi
if [[ -n "$BLOCKERS" ]]; then printf '%s' "$BLOCKERS" | sed 's/^/  BLOCK /'; fi
echo

if [[ -n "$BLOCKERS" ]]; then
  echo "Blocked: fix the items marked BLOCK above. Nothing was changed."
  exit 1
fi

if [[ $APPLY -eq 0 ]]; then
  echo "Dry run complete. Nothing was changed. Re-run with --apply to deploy."
  exit 0
fi

# ---- Apply --------------------------------------------------------------------

if [[ "$ENV_NAME" == production && $ASSUME_YES -eq 0 ]]; then
  [[ -t 0 ]] || die "refusing to deploy to production without a terminal; pass --yes to confirm non-interactively"
  printf "Type 'production' to deploy the plan above to %s: " "$HOST"
  read -r answer
  [[ "$answer" == production ]] || die "not confirmed; nothing was changed"
fi

APPLY_STARTED=1
inventory_markdown >"$WORK_DIR/inventory-before.md" 2>/dev/null || : >"$WORK_DIR/inventory-before.md"

echo "Deploying..."
APPLY_ARGS=$(printf '%q ' "$UPLOAD_DIR" "$UP_SHA" "$UP_KIND" "$UP_REFNAME" "$STUDIO_DIR" "$ST_SHA" "$ST_KIND" "$ST_REFNAME" "$CADDY_ACTION" "$CADDY_TMP" "$RUN_ID")
# Drop BuildKit's per-step progress lines from the log, but keep any that mention a problem.
remote "sudo bash -s -- $APPLY_ARGS" <<<"$APPLY_SCRIPT" 2>&1 \
  | awk '!/^#[0-9]+( |$)/ || /ERROR|[Ee]rror|[Ww]arning|failed/ {print; fflush()}' \
  | tee "$WORK_DIR/apply.log"
APPLY_STATUS=${PIPESTATUS[0]}

# Services without a healthcheck count as ready once running, but need a few more
# seconds to answer. Wait for the local endpoints before inspecting or smoke-testing.
if [[ $APPLY_STATUS -eq 0 ]]; then
  echo
  echo "Waiting for the services to answer..."
  remote "bash -s" <<<"$READY_SCRIPT" 2>&1 | tee -a "$WORK_DIR/apply.log"
fi

if live_state 2>/dev/null; then
  UP_AFTER_SHA=$UP_LIVE_SHA
  ST_AFTER_SHA=$ST_LIVE_SHA
else
  UP_AFTER_SHA="not read"
  ST_AFTER_SHA="not read"
fi
inventory_markdown >"$WORK_DIR/inventory-after.md" 2>/dev/null || : >"$WORK_DIR/inventory-after.md"

SMOKE_STATUS=0
if [[ $RUN_SMOKE -eq 1 ]]; then
  echo
  echo "Running deploy_smoke_test.sh $ENV_NAME ..."
  "$SCRIPT_DIR/deploy_smoke_test.sh" "$ENV_NAME" 2>&1 | tee "$WORK_DIR/smoke.txt"
  SMOKE_STATUS=${PIPESTATUS[0]}
fi

if [[ $APPLY_STATUS -ne 0 ]]; then
  RESULT=FAILED
  RESULT_DETAIL="the deployment step exited with status $APPLY_STATUS"
elif [[ $SMOKE_STATUS -ne 0 ]]; then
  RESULT=FAILED
  RESULT_DETAIL="deployment completed but the smoke test failed (exit $SMOKE_STATUS)"
else
  RESULT=SUCCESS
  RESULT_DETAIL=""
fi

write_record
echo "Result: $RESULT${RESULT_DETAIL:+, $RESULT_DETAIL}"
[[ "$RESULT" == SUCCESS ]]
