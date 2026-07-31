#!/usr/bin/env bash

set -euo pipefail

WEB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$WEB_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
PYTHON="$VENV_DIR/bin/python"
FRONTEND_DIR="$WEB_DIR/frontend"
DIST_INDEX="$FRONTEND_DIR/dist/index.html"

if [[ ! -x "$PYTHON" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$PYTHON" -m pip install \
  --disable-pip-version-check \
  --quiet \
  -r "$WEB_DIR/backend/requirements.txt"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]] ||
  [[ "$FRONTEND_DIR/package-lock.json" -nt "$FRONTEND_DIR/node_modules/.package-lock.json" ]]; then
  npm --prefix "$FRONTEND_DIR" ci
fi

needs_build=false
if [[ ! -f "$DIST_INDEX" ]] ||
  [[ "$FRONTEND_DIR/index.html" -nt "$DIST_INDEX" ]] ||
  [[ "$FRONTEND_DIR/package.json" -nt "$DIST_INDEX" ]] ||
  [[ "$FRONTEND_DIR/package-lock.json" -nt "$DIST_INDEX" ]] ||
  [[ "$FRONTEND_DIR/tsconfig.json" -nt "$DIST_INDEX" ]] ||
  [[ "$FRONTEND_DIR/vite.config.ts" -nt "$DIST_INDEX" ]] ||
  find "$FRONTEND_DIR/src" -type f -newer "$DIST_INDEX" -print -quit | grep -q .; then
  needs_build=true
fi

if [[ "$needs_build" == true ]]; then
  npm --prefix "$FRONTEND_DIR" run build
fi

cd "$REPO_ROOT"
echo "Report reader: http://127.0.0.1:8000"
exec "$PYTHON" -m uvicorn web.backend.app:app --host 127.0.0.1 --port 8000
