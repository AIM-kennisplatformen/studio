#!/usr/bin/env bash
set -euxo pipefail

rm -rf \
  /tmp/studio_frontend_hmr \
  /tmp/studio_frontend_hmr.pid \
  /tmp/studio_frontend_hmr.log >/dev/null 2>&1 || true

pixi run npm install --prefix src/frontend
pixi run npm run build --prefix src/frontend
