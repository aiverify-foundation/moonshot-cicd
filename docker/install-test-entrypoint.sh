#!/usr/bin/env bash
# Install-test entrypoint:
#   verify (default) — Installation Guide: API :8000 + Next dev :3000, HTTP smoke
#   serve            — same stack, keeps running for manual UI
#   e2e              — CI path: built portal on :8000 + Playwright (extra args → playwright test)

set -euo pipefail

APP_ROOT="/app"
CORE_DIR="${APP_ROOT}/moonshot_core"
PORTAL_DIR="${APP_ROOT}/moonshot_portal_app"
SYSTEM_TEST_DIR="${APP_ROOT}/system_test"
API_PORT="${API_PORT:-8000}"
PORTAL_PORT="${PORTAL_PORT:-3000}"
BASE_URL="${BASE_URL:-http://localhost:${API_PORT}}"
MAX_WAIT="${INSTALL_TEST_MAX_WAIT:-90}"
E2E_DB_PATH="${MOONSHOT_DB_PATH:-${CORE_DIR}/data/database/moonshot_e2e.db}"

API_PID=""
PORTAL_PID=""
API_LOG=""
PORTAL_LOG=""

cleanup() {
  if [[ -n "${PORTAL_PID}" ]] && kill -0 "${PORTAL_PID}" 2>/dev/null; then
    kill "${PORTAL_PID}" 2>/dev/null || true
    wait "${PORTAL_PID}" 2>/dev/null || true
  fi
  if [[ -n "${API_PID}" ]] && kill -0 "${API_PID}" 2>/dev/null; then
    kill "${API_PID}" 2>/dev/null || true
    wait "${API_PID}" 2>/dev/null || true
  fi
  rm -f "${API_LOG}" "${PORTAL_LOG}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

tail_logs_on_failure() {
  if [[ -n "${API_LOG}" && -f "${API_LOG}" ]]; then
    echo "--- FastAPI log (last 40 lines) ---" >&2
    tail -n 40 "${API_LOG}" >&2 || true
  fi
  if [[ -n "${PORTAL_LOG}" && -f "${PORTAL_LOG}" ]]; then
    echo "--- Next.js log (last 40 lines) ---" >&2
    tail -n 40 "${PORTAL_LOG}" >&2 || true
  fi
}

wait_for_url() {
  local url="$1"
  local label="$2"
  local pid="${3:-}"
  echo "Waiting for ${label} at ${url} (up to ${MAX_WAIT}s)..."
  for ((i = 1; i <= MAX_WAIT; i++)); do
    if [[ -n "${pid}" ]] && ! kill -0 "${pid}" 2>/dev/null; then
      echo "error: ${label} process exited before ready." >&2
      tail_logs_on_failure
      return 1
    fi
    if curl -sf "${url}" >/dev/null 2>&1; then
      echo "${label} is up."
      return 0
    fi
    sleep 1
  done
  echo "error: ${label} did not respond at ${url} within ${MAX_WAIT}s." >&2
  tail_logs_on_failure
  return 1
}

start_api() {
  API_LOG="$(mktemp /tmp/moonshot-api.XXXXXX.log)"
  echo "Starting FastAPI on port ${API_PORT}..."
  export PYTHONPATH="${CORE_DIR}"
  export MOONSHOT_DB_PATH="${E2E_DB_PATH}"
  cd "${CORE_DIR}"
  python run_api.py >"${API_LOG}" 2>&1 &
  API_PID=$!
  sleep 1
  if ! kill -0 "${API_PID}" 2>/dev/null; then
    echo "error: FastAPI failed to start." >&2
    tail_logs_on_failure
    exit 1
  fi
  if grep -q "Address already in use" "${API_LOG}" 2>/dev/null; then
    echo "error: FastAPI could not bind to port ${API_PORT}." >&2
    tail_logs_on_failure
    exit 1
  fi
}

start_api_for_e2e() {
  mkdir -p "$(dirname "${E2E_DB_PATH}")"
  if [[ -f "${E2E_DB_PATH}" ]]; then
    rm -f "${E2E_DB_PATH}"
  fi
  echo "Using isolated E2E database: ${E2E_DB_PATH}"
  start_api
  wait_for_url "${BASE_URL}/" "API (portal static on :${API_PORT})" "${API_PID}"
}

start_portal() {
  PORTAL_LOG="$(mktemp /tmp/moonshot-portal.XXXXXX.log)"
  echo "Starting Next.js dev on port ${PORTAL_PORT}..."
  cd "${PORTAL_DIR}"
  npm run dev -- --hostname 0.0.0.0 --port "${PORTAL_PORT}" >"${PORTAL_LOG}" 2>&1 &
  PORTAL_PID=$!
  sleep 1
  if ! kill -0 "${PORTAL_PID}" 2>/dev/null; then
    echo "error: Next.js dev server failed to start." >&2
    tail_logs_on_failure
    exit 1
  fi
  wait_for_url "http://localhost:${PORTAL_PORT}/" "Portal" "${PORTAL_PID}"
}

verify_portal_landing() {
  local html
  html="$(curl -sf "http://localhost:${PORTAL_PORT}/")"
  if echo "${html}" | grep -q 'Run a benchmark test'; then
    echo "Portal landing page content OK."
    return 0
  fi
  if echo "${html}" | grep -q 'data-testid="benchmark-link"'; then
    echo "Portal landing page content OK."
    return 0
  fi
  echo "error: portal HTML missing expected landing content." >&2
  return 1
}

verify_backend() {
  curl -sf "${BASE_URL}/api/bundles" >/dev/null
  echo "API /api/bundles OK."
}

seed_e2e_data() {
  echo "Seeding E2E test data via API..."
  export BASE_URL
  python "${SYSTEM_TEST_DIR}/scripts/seed_e2e_data.py"
}

run_playwright() {
  echo "Running Playwright system tests..."
  cd "${SYSTEM_TEST_DIR}"
  export BASE_URL
  export E2E_PYTHON="${E2E_PYTHON:-/app/moonshot-env/bin/python}"
  export CI="${CI:-true}"
  if [[ $# -gt 0 ]]; then
    npx playwright test "$@"
  else
    npm run test
  fi
}

cmd_verify() {
  export MOONSHOT_DB_PATH="${CORE_DIR}/data/database/moonshot_install_test.db"
  E2E_DB_PATH="${MOONSHOT_DB_PATH}"
  start_api
  wait_for_url "${BASE_URL}/api/bundles" "API" "${API_PID}"
  start_portal
  verify_backend
  verify_portal_landing
  echo "Install verification passed (frontend + backend)."
}

cmd_serve() {
  export MOONSHOT_DB_PATH="${CORE_DIR}/data/database/moonshot_install_test.db"
  E2E_DB_PATH="${MOONSHOT_DB_PATH}"
  start_api
  wait_for_url "${BASE_URL}/api/bundles" "API" "${API_PID}"
  start_portal
  echo "Moonshot web UI: http://localhost:${PORTAL_PORT}"
  echo "API: http://localhost:${API_PORT}"
  echo "Press Ctrl+C to stop."
  while true; do
    if [[ -n "${API_PID}" ]] && ! kill -0 "${API_PID}" 2>/dev/null; then
      echo "error: FastAPI exited." >&2
      tail_logs_on_failure
      exit 1
    fi
    if [[ -n "${PORTAL_PID}" ]] && ! kill -0 "${PORTAL_PID}" 2>/dev/null; then
      echo "error: Next.js dev server exited." >&2
      tail_logs_on_failure
      exit 1
    fi
    sleep 2
  done
}

cmd_e2e() {
  # Optional: consume leading "--" from "docker run ... e2e -- --headed"
  if [[ "${1:-}" == "--" ]]; then
    shift
  fi
  E2E_DB_PATH="${CORE_DIR}/data/database/moonshot_e2e.db"
  export MOONSHOT_DB_PATH="${E2E_DB_PATH}"
  start_api_for_e2e
  seed_e2e_data
  run_playwright "$@"
  echo "E2E tests finished successfully."
}

MODE="${1:-verify}"
shift || true
case "${MODE}" in
  verify) cmd_verify ;;
  serve) cmd_serve ;;
  e2e) cmd_e2e "$@" ;;
  *)
    echo "usage: $0 [verify|serve|e2e] [-- playwright args...]" >&2
    exit 1
    ;;
esac
