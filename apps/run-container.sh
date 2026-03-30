#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-investment-agent-web}"
CONTAINER_NAME="${CONTAINER_NAME:-investment-agent-web}"
WEB_PORT="${WEB_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
AGENT_PORT="${AGENT_PORT:-9002}"
DETACH="${DETACH:-0}"

cd "${ROOT_DIR}"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  echo "[run] image '${IMAGE_NAME}' not found, building first"
  "${ROOT_DIR}/apps/build-container.sh"
fi

if docker ps -a --format '{{.Names}}' | grep -Fx "${CONTAINER_NAME}" >/dev/null 2>&1; then
  echo "[run] removing existing container: ${CONTAINER_NAME}"
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

RUN_ARGS=(
  --name "${CONTAINER_NAME}"
  -p "${WEB_PORT}:3000"
  -p "${BACKEND_PORT}:8000"
  -p "${AGENT_PORT}:9002"
)

if [[ "${DETACH}" == "1" ]]; then
  RUN_ARGS=(-d "${RUN_ARGS[@]}")
else
  RUN_ARGS=(--rm "${RUN_ARGS[@]}")
fi

echo "[run] starting container: ${CONTAINER_NAME}"
docker run "${RUN_ARGS[@]}" "${IMAGE_NAME}"
