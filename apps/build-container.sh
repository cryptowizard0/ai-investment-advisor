#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-investment-agent-web}"

cd "${ROOT_DIR}"

echo "[build] building docker image: ${IMAGE_NAME}"
docker build -t "${IMAGE_NAME}" .

echo "[build] done"
