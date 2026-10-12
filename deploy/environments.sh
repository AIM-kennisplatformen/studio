#!/usr/bin/env bash
# shellcheck shell=bash disable=SC2034,SC2029
# Environment definitions shared by deploy.sh and deploy_smoke_test.sh.
# Source this file; do not run it.
#
# SCEPA_SSH_USER   Optional. SSH login name on the VMs. When unset, ssh uses
#                  its own defaults (~/.ssh/config, then the local user name).

AUTH_HOST=authscepa.mads-han.src.surf-hosted.nl

load_environment() {
  case "${1:-}" in
    staging)
      ENV_NAME=staging
      HOST=kpscepastaging.mads-han.src.surf-hosted.nl
      TARGET_BRANCH=current-staging
      ;;
    production)
      ENV_NAME=production
      HOST=scepakp.mads-han.src.surf-hosted.nl
      TARGET_BRANCH=current-production
      ;;
    *)
      echo "error: environment must be 'staging' or 'production' (got '${1:-}')" >&2
      return 2
      ;;
  esac

  BASE_URL="https://$HOST"
  OAUTH_CALLBACK="$BASE_URL/chatep/api/auth/callback"

  UPLOAD_DIR=/srv/share/upload-interface
  UPLOAD_REPO=AIM-kennisplatformen/database-builder-scepa-rs
  STUDIO_DIR=/srv/share/studio
  STUDIO_REPO=AIM-kennisplatformen/studio

  SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ServerAliveCountMax=40
    -o ControlMaster=auto -o ControlPersist=300 -o "ControlPath=/tmp/scepa-ssh-%C")
  if [[ -n "${SCEPA_SSH_USER:-}" ]]; then
    SSH_OPTS+=(-l "$SCEPA_SSH_USER")
  fi
}

# remote <command...>: run a command on the selected environment's VM.
remote() {
  ssh "${SSH_OPTS[@]}" "$HOST" "$@"
}

SSH_MASTER_OWNED=0

# open_ssh: open one shared SSH connection that every later remote call reuses.
# A login can fail for a moment while the VM rewrites ~/.ssh/authorized_keys, so
# the connection step is retried; calls that reuse the connection do not log in
# again. Returns 1 when the VM stays unreachable.
open_ssh() {
  local attempt
  if ssh "${SSH_OPTS[@]}" -O check "$HOST" >/dev/null 2>&1; then
    return 0 # another script already opened it; leave it to that script to close
  fi
  for attempt in 1 2 3 4 5; do
    if ssh "${SSH_OPTS[@]}" "$HOST" true </dev/null >/dev/null 2>&1; then
      SSH_MASTER_OWNED=1
      return 0
    fi
    sleep 3
  done
  return 1
}

# close_ssh: close the shared connection if this script opened it.
close_ssh() {
  if [[ "$SSH_MASTER_OWNED" -eq 1 ]]; then
    ssh "${SSH_OPTS[@]}" -O exit "$HOST" >/dev/null 2>&1 || true
    SSH_MASTER_OWNED=0
  fi
}
