#!/usr/bin/env bash
# deploy_smoke_test.sh <staging|production>
#
# Read-only health check of one environment: public routes and TLS from this
# machine, then service, container, endpoint, data and configuration checks on
# the VM over SSH. It changes nothing. deploy.sh runs it after every deployment,
# and you can run it at any time (after a reboot, before a deployment).
#
# Exit status: 0 when nothing failed (warnings allowed), 1 when any check
# failed, 2 for bad usage or when the VM cannot be reached.
#
# Needs: bash, curl, openssl, ssh. Secrets (MCP bearer token, Qdrant key) are
# read on the VM and never leave it. Set SCEPA_SSH_USER if your SSH login name
# differs from your local user name.

set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=environments.sh
source "$SCRIPT_DIR/environments.sh"

if [[ $# -ne 1 ]]; then
  echo "usage: ${0##*/} <staging|production>" >&2
  exit 2
fi
load_environment "$1" || exit 2
trap close_ssh EXIT

PASSES=0
FAILS=0
WARNS=0

report() { # status name detail
  case "$1" in
    PASS) PASSES=$((PASSES + 1)) ;;
    FAIL) FAILS=$((FAILS + 1)) ;;
    WARN) WARNS=$((WARNS + 1)) ;;
  esac
  printf '%-5s %-36s %s\n' "$1" "$2" "${3:-}"
}

expect_http() { # name url expected-code [expected-redirect]
  local out code loc
  if ! out=$(curl -sS --max-time 20 -o /dev/null -w '%{http_code} %{redirect_url}' "$2" 2>&1); then
    report FAIL "$1" "curl failed: $out"
    return
  fi
  code=${out%% *}
  loc=${out#* }
  if [[ "$code" != "$3" ]]; then
    report FAIL "$1" "HTTP $code, expected $3"
    return
  fi
  if [[ -n "${4:-}" && "$loc" != "$4" ]]; then
    report FAIL "$1" "redirects to '$loc', expected '$4'"
    return
  fi
  report PASS "$1" "HTTP $code${loc:+ -> $loc}"
}

urldecode() {
  local v=${1//+/ }
  printf '%b' "${v//%/\\x}"
}

echo "Smoke test: $ENV_NAME ($HOST)  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

# ---- From this machine --------------------------------------------------------

expect_http "public /" "$BASE_URL/" 302 "$BASE_URL/chatep"
expect_http "public /chatep/" "$BASE_URL/chatep/" 200
expect_http "public /upload/" "$BASE_URL/upload/" 200
expect_http "public /mcp without token" "$BASE_URL/mcp" 401

# TLS certificate lifetime.
cert=$(echo | openssl s_client -connect "$HOST:443" -servername "$HOST" 2>/dev/null | openssl x509 2>/dev/null)
if [[ -z "$cert" ]]; then
  report FAIL "TLS certificate" "no certificate presented on $HOST:443"
else
  not_after=$(printf '%s\n' "$cert" | openssl x509 -noout -enddate | cut -d= -f2)
  if ! printf '%s\n' "$cert" | openssl x509 -noout -checkend $((10 * 86400)) >/dev/null; then
    report FAIL "TLS certificate" "expires within 10 days (notAfter $not_after)"
  elif ! printf '%s\n' "$cert" | openssl x509 -noout -checkend $((21 * 86400)) >/dev/null; then
    report WARN "TLS certificate" "expires within 21 days (notAfter $not_after); Caddy should renew"
  else
    report PASS "TLS certificate" "valid until $not_after"
  fi
fi

# Studio login must send users to the right Authentik client and callback.
login=$(curl -sS --max-time 20 -o /dev/null -w '%{http_code} %{redirect_url}' "$BASE_URL/chatep/api/auth/login" 2>&1)
login_code=${login%% *}
login_url=${login#* }
if [[ "$login_code" != 302 ]]; then
  report FAIL "oauth login redirect" "HTTP $login_code, expected 302"
elif [[ "$login_url" != "https://$AUTH_HOST/application/o/authorize/"* ]]; then
  report FAIL "oauth login redirect" "redirects to an unexpected place: ${login_url%%\?*}"
else
  query=${login_url#*\?}
  redirect_uri=""
  client_id=""
  IFS='&' read -r -a parts <<<"$query"
  for part in "${parts[@]}"; do
    case "$part" in
      redirect_uri=*) redirect_uri=$(urldecode "${part#redirect_uri=}") ;;
      client_id=*) client_id=${part#client_id=} ;;
    esac
  done
  if [[ -z "$client_id" ]]; then
    report FAIL "oauth login redirect" "no client_id in the authorize request"
  elif [[ "$redirect_uri" != "$OAUTH_CALLBACK" ]]; then
    report FAIL "oauth login redirect" "redirect_uri is '$redirect_uri', expected '$OAUTH_CALLBACK'"
  else
    report PASS "oauth login redirect" "Authentik client set, callback $OAUTH_CALLBACK"
  fi
fi

# ---- On the VM ----------------------------------------------------------------

if ! open_ssh; then
  report FAIL "ssh" "cannot reach $HOST over SSH, VM checks skipped"
  echo
  echo "Result: $PASSES passed, $WARNS warnings, $FAILS failed"
  exit 2
fi

# The heredoc sits outside any command substitution on purpose: bash 3.2 (the
# macOS default) cannot parse a "case" block inside $( ... <<EOF ... ).
read -r -d '' REMOTE_CHECKS <<'REMOTE'
set -u
emit() { printf '%s|%s|%s\n' "$1" "$2" "$3"; }
http_code() { curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$@"; }
check_http() { # name url expected
  local c
  c=$(http_code "$2")
  if [ "$c" = "$3" ]; then emit PASS "$1" "HTTP $c"; else emit FAIL "$1" "HTTP $c, expected $3"; fi
}
env_of() { grep -m1 "^$2=" "$1" 2>/dev/null | cut -d= -f2-; }

# System services.
for s in docker containerd caddy fail2ban; do
  st=$(systemctl is-active "$s" 2>&1)
  if [ "$st" = active ]; then emit PASS "service $s" active; else emit FAIL "service $s" "$st"; fi
done

# Disk space under Docker's data root.
root=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null)
if [ -n "$root" ]; then
  used=$(df --output=pcent "$root" | tail -1 | tr -dc '0-9')
  if [ "$used" -ge 95 ]; then emit FAIL "disk $root" "${used}% used"
  elif [ "$used" -ge 85 ]; then emit WARN "disk $root" "${used}% used"
  else emit PASS "disk $root" "${used}% used"; fi
else
  emit FAIL "disk" "cannot read Docker's data root"
fi

# Compose stacks: every service running, healthchecks healthy.
for d in "$UPLOAD_DIR" "$STUDIO_DIR"; do
  name=$(basename "$d")
  if ! cd "$d" 2>/dev/null; then emit FAIL "stack $name" "$d is missing"; continue; fi
  services=$(docker compose -f compose.release.yaml config --services 2>/dev/null)
  ps=$(docker compose -f compose.release.yaml ps --all --format '{{.Service}} {{.State}} {{.Health}}' 2>/dev/null)
  bad=""
  n=0
  for s in $services; do
    n=$((n + 1))
    line=$(printf '%s\n' "$ps" | awk -v s="$s" '$1 == s {print; exit}')
    state=$(printf '%s\n' "$line" | awk '{print $2}')
    health=$(printf '%s\n' "$line" | awk '{print $3}')
    if [ "$state" != running ]; then bad="$bad $s(${state:-missing})"
    elif [ -n "$health" ] && [ "$health" != healthy ]; then bad="$bad $s($health)"; fi
  done
  if [ "$n" -eq 0 ]; then emit FAIL "stack $name" "no services found in compose.release.yaml"
  elif [ -z "$bad" ]; then emit PASS "stack $name" "$n services running, healthchecks healthy"
  else emit FAIL "stack $name" "not healthy:$bad"; fi
  restarts=$(docker compose -f compose.release.yaml ps -q 2>/dev/null | xargs -r docker inspect -f '{{.Name}} {{.RestartCount}}' 2>/dev/null | awk '$2 >= 3 {printf "%s(%s) ", substr($1,2), $2}')
  [ -n "$restarts" ] && emit WARN "restarts $name" "containers that restarted 3+ times: $restarts"
done

# Local endpoints.
check_http "mcp /health" http://127.0.0.1:8002/health 200
check_http "api /openapi.json" http://127.0.0.1:3000/openapi.json 200
check_http "upload frontend" http://127.0.0.1:5173/upload/ 200
check_http "studio frontend" http://127.0.0.1:10090/chatep/ 200
check_http "studio api /api/docs" http://127.0.0.1:10092/api/docs 200
check_http "typedb /health" http://127.0.0.1:8000/health 204

# MCP authentication and tool list (no embedding calls, so no Nebius cost).
tok=$(env_of "$UPLOAD_DIR/.env" MCP_BEARER_TOKEN)
if [ -z "$tok" ]; then
  emit FAIL "mcp token" "MCP_BEARER_TOKEN is missing in $UPLOAD_DIR/.env"
else
  U=http://127.0.0.1:8002/mcp
  c=$(printf 'header = "Authorization: Bearer wrong-token"\n' | curl -s -K - -o /dev/null -w '%{http_code}' --max-time 20 -X POST "$U" -d '{}')
  if [ "$c" = 401 ]; then emit PASS "mcp rejects a wrong token" "HTTP 401"; else emit FAIL "mcp rejects a wrong token" "HTTP $c, expected 401"; fi
  hf=$(mktemp)
  hdr() {
    printf 'header = "Authorization: Bearer %s"\nheader = "Content-Type: application/json"\nheader = "Accept: application/json, text/event-stream"\n' "$tok"
    [ -n "${sid:-}" ] && printf 'header = "Mcp-Session-Id: %s"\n' "$sid"
  }
  sid=""
  hdr | curl -s -K - -D "$hf" -o /dev/null --max-time 30 -X POST "$U" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}'
  code=$(head -1 "$hf" | tr -d '\r' | awk '{print $2}')
  sid=$(grep -i '^mcp-session-id:' "$hf" | cut -d' ' -f2 | tr -d '\r')
  rm -f "$hf"
  if [ "$code" != 200 ]; then
    emit FAIL "mcp accepts the token" "initialize returned HTTP ${code:-none}"
  else
    hdr | curl -s -K - -o /dev/null --max-time 15 -X POST "$U" -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
    tools=$(hdr | curl -s -K - --max-time 30 -X POST "$U" -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | sed -n 's/^data: //p;/^{/p' | head -1 | jq -r '[.result.tools[]?.name] | join(",")' 2>/dev/null)
    case ",$tools," in
      *,search_literature,*) emit PASS "mcp accepts the token" "tools: $tools" ;;
      *) emit FAIL "mcp accepts the token" "search_literature not listed (got: ${tools:-nothing})" ;;
    esac
  fi
fi

# Qdrant collection.
qk=$(env_of "$UPLOAD_DIR/.env" QDRANT_API_KEY)
q=$(printf 'header = "api-key: %s"\n' "$qk" | curl -s -K - --max-time 20 http://127.0.0.1:6333/collections/scepa)
status=$(printf '%s' "$q" | jq -r '.result.status // empty' 2>/dev/null)
points=$(printf '%s' "$q" | jq -r '.result.points_count // empty' 2>/dev/null)
if [ "$status" != green ]; then emit FAIL "qdrant collection scepa" "status '${status:-unreadable}'"
elif [ "${points:-0}" -eq 0 ]; then emit WARN "qdrant collection scepa" "green but empty"
else emit PASS "qdrant collection scepa" "green, $points points"; fi

# Restate: workflows registered, nothing stuck.
svc=$(curl -s --max-time 20 http://127.0.0.1:9070/deployments | jq -r '[.deployments[]?.services[]?.name] | join(",")' 2>/dev/null)
case ",$svc," in
  *,NewDocumentWorkflow,*) emit PASS "restate deployment" "workflows registered" ;;
  *) emit FAIL "restate deployment" "NewDocumentWorkflow is not registered (got: ${svc:-nothing})" ;;
esac
rq() { curl -s --max-time 20 http://127.0.0.1:9070/query -H 'accept: application/json' -H 'content-type: application/json' -d "{\"query\":\"$1\"}"; }
stuck=$(rq "select count(*) as n from sys_invocation where status in ('paused','backing-off')" | jq -r '.rows[0].n // empty' 2>/dev/null)
active=$(rq "select count(*) as n from sys_invocation where status <> 'completed'" | jq -r '.rows[0].n // empty' 2>/dev/null)
if [ -z "$stuck" ]; then emit FAIL "restate invocations" "cannot query sys_invocation"
elif [ "$stuck" -gt 0 ]; then emit WARN "restate invocations" "$stuck paused or backing off, $active not completed"
else emit PASS "restate invocations" "none stuck, $active in flight"; fi

# Data reachable through the API.
docs=$(curl -s --max-time 30 http://127.0.0.1:3000/documents | jq 'length' 2>/dev/null)
if [ -z "$docs" ]; then emit FAIL "api /documents" "response is not a JSON list"
elif [ "$docs" -eq 0 ]; then emit WARN "api /documents" "returns no documents"
else emit PASS "api /documents" "$docs documents"; fi

# Studio configuration inside the running backend container.
cd "$STUDIO_DIR" 2>/dev/null || true
benv() { docker compose -f compose.release.yaml exec -T backend printenv "$1" </dev/null 2>/dev/null | tr -d '\r'; }
v=$(benv LANGFUSE_TRACING_ENVIRONMENT)
if [ "$v" = "$EXPECT_ENV" ]; then emit PASS "langfuse environment" "LANGFUSE_TRACING_ENVIRONMENT=$v"
else emit FAIL "langfuse environment" "backend has '${v:-<unset>}', expected '$EXPECT_ENV'"; fi
v=$(benv OAUTH_REDIRECT_URI)
if [ "$v" = "$EXPECT_CALLBACK" ]; then emit PASS "backend OAUTH_REDIRECT_URI" "matches $EXPECT_CALLBACK"
else emit FAIL "backend OAUTH_REDIRECT_URI" "is '${v:-<unset>}', expected '$EXPECT_CALLBACK'"; fi
disc=$(benv OAUTH_DISCOVERY_URL)
if [ -z "$disc" ]; then emit FAIL "oauth discovery" "OAUTH_DISCOVERY_URL is unset in the backend"
else
  c=$(http_code "$disc")
  if [ "$c" = 200 ]; then emit PASS "oauth discovery" "HTTP 200"; else emit FAIL "oauth discovery" "HTTP $c from the discovery URL"; fi
fi
c=$(docker compose -f compose.release.yaml exec -T backend pixi run python -c 'import urllib.request as u; print(u.urlopen("http://host.docker.internal:8002/health", timeout=10).status)' </dev/null 2>/dev/null | tail -1 | tr -d '\r')
if [ "$c" = 200 ]; then emit PASS "studio backend -> mcp" "host.docker.internal:8002 answers HTTP 200"
else emit FAIL "studio backend -> mcp" "host.docker.internal:8002 gave '${c:-no response}'"; fi

# Git state of both checkouts.
for d in "$UPLOAD_DIR" "$STUDIO_DIR"; do
  o=$(stat -c %U "$d")
  g() { sudo -u "$o" git -C "$d" "$@"; }
  head=$(g rev-parse --short HEAD 2>/dev/null)
  branch=$(g rev-parse --abbrev-ref HEAD 2>/dev/null)
  dirty=$(g status --porcelain --untracked-files=no 2>/dev/null | wc -l)
  if [ "$dirty" -gt 0 ]; then emit WARN "git $(basename "$d")" "$branch at $head has $dirty modified tracked files"
  else emit PASS "git $(basename "$d")" "$branch at $head, clean"; fi
done
REMOTE

remote_output=$(remote "sudo env EXPECT_ENV='$ENV_NAME' EXPECT_CALLBACK='$OAUTH_CALLBACK' UPLOAD_DIR='$UPLOAD_DIR' STUDIO_DIR='$STUDIO_DIR' bash -s" <<<"$REMOTE_CHECKS")
remote_status=$?

if [[ $remote_status -ne 0 && -z "$remote_output" ]]; then
  report FAIL "vm checks" "the SSH session failed (exit $remote_status)"
fi

while IFS='|' read -r status name detail; do
  [[ -n "$status" ]] && report "$status" "$name" "$detail"
done <<<"$remote_output"

echo
echo "Result: $PASSES passed, $WARNS warnings, $FAILS failed"
if [[ $FAILS -gt 0 ]]; then
  exit 1
fi
exit 0
