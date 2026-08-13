#!/usr/bin/env bash
set -euxo pipefail

hmr_dir="${FRONTEND_HMR_MARKER:-/tmp/studio_frontend_hmr}"
pid_file="/tmp/studio_frontend_hmr.pid"
log_file="/tmp/studio_frontend_hmr.log"
vite_cache_dir="/tmp/studio_vite_cache"
vite_pattern="[v]ite.*--host 0.0.0.0"

cleanup() {
  rm -rf "$hmr_dir" "$pid_file" "$log_file" "$vite_cache_dir"
  if [ -n "${vite_pid:-}" ]; then
    kill "$vite_pid" 2>/dev/null || true
    wait "$vite_pid" 2>/dev/null || true
  fi
  pkill -f "$vite_pattern" 2>/dev/null || true
}

trap cleanup EXIT INT TERM HUP

cleanup

mkdir -p "$hmr_dir"
CHOKIDAR_USEPOLLING=true WATCHPACK_POLLING=true VITE_CACHE_DIR="$vite_cache_dir" pixi run npm --prefix src/frontend run dev -- --host 0.0.0.0 &
vite_pid=$!
echo "$vite_pid" > "$pid_file"
wait "$vite_pid"
