#!/usr/bin/env bash
# Host Moonshot with one Docker named volume (DB + benchmark results).
#
#   ./docker/serve.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${MOONSHOT_INSTALL_TEST_IMAGE:-moonshot-install-test}"
DATA_VOLUME="${MOONSHOT_DATA_VOLUME:-moonshot-install-test-data}"
DATA_MOUNT="/var/lib/moonshot"
DB_PATH="${DATA_MOUNT}/moonshot_install_test.db"
RESULTS_PATH="${DATA_MOUNT}/results"

ensure_image() {
  if [[ "${MOONSHOT_INSTALL_TEST_SKIP_BUILD:-}" == "1" ]]; then
    echo "Skipping image build check (MOONSHOT_INSTALL_TEST_SKIP_BUILD=1)."
    return 0
  fi
  if docker image inspect "${IMAGE}" >/dev/null 2>&1; then
    echo "Docker image '${IMAGE}' found."
    return 0
  fi
  echo "Docker image '${IMAGE}' not found. Building from docker/moonshot.install-test.Dockerfile (first time may take several minutes)..."
  docker build -f "${ROOT}/docker/moonshot.install-test.Dockerfile" -t "${IMAGE}" "${ROOT}"
  echo "Docker image '${IMAGE}' built."
}

ensure_volume() {
  local name="$1"
  if docker volume inspect "${name}" >/dev/null 2>&1; then
    echo "Docker volume '${name}' already exists."
  else
    docker volume create "${name}"
    echo "Docker volume '${name}' created."
  fi
}

ensure_image
echo ""
echo "Persistent storage (one named volume):"
ensure_volume "${DATA_VOLUME}"
echo "  Mount: ${DATA_MOUNT}"
echo "  DB: ${DB_PATH}"
echo "  Results: ${RESULTS_PATH}"
echo "  List: docker volume ls | grep moonshot-install-test"
echo ""

ENV_ARGS=()
for var in OPENAI_API_KEY TOGETHER_API_KEY ANTHROPIC_API_KEY MS_CORS_ORIGINS MS_LOG_LEVEL; do
  if [[ -n "${!var:-}" ]]; then
    ENV_ARGS+=(-e "${var}=${!var}")
  fi
done
if [[ -f "${ROOT}/.env" ]]; then
  ENV_ARGS+=(--env-file "${ROOT}/.env")
fi
# After --env-file so a .env MOONSHOT_DB_PATH cannot point at an ephemeral path in the container
ENV_ARGS+=(
  -e "MOONSHOT_DB_PATH=${DB_PATH}"
  -e "MOONSHOT_BENCHMARK_RESULTS_DIR=${RESULTS_PATH}"
  -e MOONSHOT_API_NO_RELOAD=1
)

exec docker run --rm \
  -p 8000:8000 \
  -p 3000:3000 \
  -v "${DATA_VOLUME}:${DATA_MOUNT}" \
  "${ENV_ARGS[@]}" \
  "${IMAGE}" serve "$@"
