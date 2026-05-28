#!/usr/bin/env bash
set -euo pipefail

docker compose exec -T application rm -rf \
  /tmp/studio_frontend_hmr \
  /tmp/studio_frontend_hmr.pid \
  /tmp/studio_frontend_hmr.log >/dev/null 2>&1 || true

npm run build --prefix src/frontend
