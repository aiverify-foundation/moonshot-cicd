#!/usr/bin/env bash
# Run Moonshot Playwright system tests (portal build + API on :8000 + system_test).
#
# Usage:
#   ./run-e2e-tests.sh                    # full flow
#   ./run-e2e-tests.sh --headed           # extra args passed to Playwright
#   SKIP_PORTAL_BUILD=1 ./run-e2e-tests.sh
#
# Requires: conda env moonshotv1test (see .cursorrules), Node.js 18+, npm.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_ENV="${MOONSHOT_CONDA_ENV:-moonshotv1test}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_PORT="${API_PORT:-8000}"
E2E_DB_PATH="${MOONSHOT_DB_PATH:-${ROOT}/moonshot_core/data/database/moonshot_e2e.db}"
FASTAPI_PID=""
FASTAPI_LOG=""

cleanup() {
  if [[ -n "${FASTAPI_PID}" ]] && kill -0 "${FASTAPI_PID}" 2>/dev/null; then
    echo "Stopping FastAPI (pid ${FASTAPI_PID})..."
    kill "${FASTAPI_PID}" 2>/dev/null || true
    wait "${FASTAPI_PID}" 2>/dev/null || true
  fi
  if [[ -n "${FASTAPI_LOG}" && -f "${FASTAPI_LOG}" ]]; then
    rm -f "${FASTAPI_LOG}"
  fi
}
trap cleanup EXIT INT TERM

activate_conda_env() {
  if [[ "${CONDA_DEFAULT_ENV:-}" == "${CONDA_ENV}" ]]; then
    echo "Using active conda env: ${CONDA_ENV}"
    return 0
  fi

  if command -v conda >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    eval "$(conda shell.bash hook)"
    conda activate "${CONDA_ENV}"
    echo "Activated conda env: ${CONDA_ENV}"
    return 0
  fi

  for candidate in \
    "${HOME}/miniconda3" \
    "${HOME}/anaconda3" \
    "${HOME}/miniforge3" \
    "${HOME}/mambaforge" \
    "/opt/homebrew/Caskroom/miniconda/base"; do
    if [[ -f "${candidate}/etc/profile.d/conda.sh" ]]; then
      # shellcheck disable=SC1091
      source "${candidate}/etc/profile.d/conda.sh"
      conda activate "${CONDA_ENV}"
      echo "Activated conda env: ${CONDA_ENV}"
      return 0
    fi
  done

  echo "error: could not activate conda env '${CONDA_ENV}'." >&2
  echo "Install conda or run: conda activate ${CONDA_ENV} && $0 $*" >&2
  exit 1
}

prepare_e2e_database() {
  mkdir -p "$(dirname "${E2E_DB_PATH}")"
  if [[ -f "${E2E_DB_PATH}" ]]; then
    rm -f "${E2E_DB_PATH}"
  fi
  export MOONSHOT_DB_PATH="${E2E_DB_PATH}"
  echo "Using isolated E2E database: ${MOONSHOT_DB_PATH}"
}

stop_existing_api_on_port() {
  local pids=""
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti tcp:"${API_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  fi
  if [[ -z "${pids}" ]]; then
    return 0
  fi
  echo "Stopping existing process(es) listening on port ${API_PORT}: ${pids}"
  # shellcheck disable=SC2086
  kill ${pids} 2>/dev/null || true
  sleep 1
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti tcp:"${API_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "${pids}" ]]; then
      echo "error: port ${API_PORT} is still in use after stop attempt (pid(s): ${pids})." >&2
      exit 1
    fi
  fi
}

wait_for_server() {
  local url="${BASE_URL}/"
  local max_attempts=60
  echo "Waiting for server at ${url}..."
  for ((i = 1; i <= max_attempts; i++)); do
    if [[ -n "${FASTAPI_PID}" ]] && ! kill -0 "${FASTAPI_PID}" 2>/dev/null; then
      echo "error: FastAPI process (pid ${FASTAPI_PID}) exited before the server became ready." >&2
      if [[ -f "${FASTAPI_LOG}" ]]; then
        echo "FastAPI log:" >&2
        tail -n 40 "${FASTAPI_LOG}" >&2 || true
      fi
      exit 1
    fi
    if curl -sf "${url}" >/dev/null 2>&1; then
      if [[ -n "${FASTAPI_PID}" ]] && kill -0 "${FASTAPI_PID}" 2>/dev/null; then
        echo "Server is up (FastAPI pid ${FASTAPI_PID})."
        return 0
      fi
      echo "error: ${url} responded but FastAPI pid ${FASTAPI_PID} is not running." >&2
      exit 1
    fi
    sleep 1
  done
  echo "error: server did not respond at ${url} within ${max_attempts}s." >&2
  if [[ -f "${FASTAPI_LOG}" ]]; then
    echo "FastAPI log:" >&2
    tail -n 40 "${FASTAPI_LOG}" >&2 || true
  fi
  exit 1
}

build_portal() {
  echo "Building moonshot_portal_app..."
  cd "${ROOT}/moonshot_portal_app"
  npm install
  npm run build
}

start_api() {
  stop_existing_api_on_port
  echo "Starting FastAPI on port ${API_PORT}..."
  export PYTHONPATH="${ROOT}/moonshot_core"
  export MOONSHOT_DB_PATH="${E2E_DB_PATH}"
  FASTAPI_LOG="$(mktemp "${TMPDIR:-/tmp}/moonshot-e2e-api.XXXXXX.log")"
  cd "${ROOT}/moonshot_core"
  python run_api.py >"${FASTAPI_LOG}" 2>&1 &
  FASTAPI_PID=$!
  sleep 1
  if ! kill -0 "${FASTAPI_PID}" 2>/dev/null; then
    echo "error: FastAPI failed to start (pid ${FASTAPI_PID})." >&2
    if [[ -f "${FASTAPI_LOG}" ]]; then
      cat "${FASTAPI_LOG}" >&2
    fi
    exit 1
  fi
  if grep -q "Address already in use" "${FASTAPI_LOG}" 2>/dev/null; then
    echo "error: FastAPI could not bind to port ${API_PORT}." >&2
    cat "${FASTAPI_LOG}" >&2
    exit 1
  fi
}

seed_e2e_data() {
  echo "Seeding E2E test data via API..."
  export BASE_URL
  python "${ROOT}/system_test/scripts/seed_e2e_data.py"
}

run_playwright() {
  echo "Running Playwright system tests..."
  cd "${ROOT}/system_test"
  npm install
  npx playwright install chromium
  export BASE_URL
  export E2E_PYTHON="${CONDA_PREFIX:-}/bin/python"
  if [[ ! -x "${E2E_PYTHON}" ]]; then
    E2E_PYTHON="$(command -v python)"
    export E2E_PYTHON
  fi
  if [[ $# -gt 0 ]]; then
    npx playwright test "$@"
  else
    npm run test
  fi
}

main() {
  activate_conda_env
  prepare_e2e_database
  if [[ -z "${SKIP_PORTAL_BUILD:-}" ]]; then
    build_portal
  else
    echo "Skipping portal build (SKIP_PORTAL_BUILD is set)."
  fi
  start_api
  wait_for_server
  seed_e2e_data
  run_playwright "$@"
}

main "$@"
