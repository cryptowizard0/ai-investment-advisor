#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/app"
AGENT_PORT="${AGENT_PORT:-9002}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

export AGENT_SERVICE_URL="${AGENT_SERVICE_URL:-http://127.0.0.1:${AGENT_PORT}}"
export BACKEND_API_URL="${BACKEND_API_URL:-http://127.0.0.1:${BACKEND_PORT}}"
export HOSTNAME="0.0.0.0"

cd "${ROOT_DIR}"

echo "[stack] starting agent on :${AGENT_PORT}"
python -m uvicorn app.main:app --app-dir apps/agent --host 0.0.0.0 --port "${AGENT_PORT}" &
AGENT_PID=$!

echo "[stack] starting backend on :${BACKEND_PORT}"
python -m uvicorn app.main:app --app-dir apps/backend --host 0.0.0.0 --port "${BACKEND_PORT}" &
BACKEND_PID=$!

echo "[stack] starting web on :${WEB_PORT}"
pnpm --dir apps/web dev --hostname 0.0.0.0 --port "${WEB_PORT}" &
WEB_PID=$!

cleanup() {
  echo "[stack] shutting down"
  kill "${WEB_PID}" "${BACKEND_PID}" "${AGENT_PID}" 2>/dev/null || true
  wait "${WEB_PID}" "${BACKEND_PID}" "${AGENT_PID}" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

wait -n "${AGENT_PID}" "${BACKEND_PID}" "${WEB_PID}"
