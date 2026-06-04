#!/usr/bin/env bash
# Install-test entrypoint: FastAPI (:8000) + Next dev (:3000) per Installation Guide.
# Next.js must bind 0.0.0.0 inside Docker (guide uses localhost on the host).

set -euo pipefail

APP_ROOT="/app"
CORE_DIR="${APP_ROOT}/moonshot_core"
PORTAL_DIR="${APP_ROOT}/moonshot_portal_app"
API_PORT="${API_PORT:-8000}"
PORTAL_PORT="${PORTAL_PORT:-3000}"
MAX_WAIT="${INSTALL_TEST_MAX_WAIT:-90}"

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
  cd "${CORE_DIR}"
  python run_api.py >"${API_LOG}" 2>&1 &
  API_PID=$!
  sleep 1
  if ! kill -0 "${API_PID}" 2>/dev/null; then
    echo "error: FastAPI failed to start." >&2
    tail_logs_on_failure
    exit 1
  fi
  wait_for_url "http://127.0.0.1:${API_PORT}/api/bundles" "API" "${API_PID}"
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
  wait_for_url "http://127.0.0.1:${PORTAL_PORT}/" "Portal" "${PORTAL_PID}"
}

verify_portal_landing() {
  local html
  html="$(curl -sf "http://127.0.0.1:${PORTAL_PORT}/")"
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
  curl -sf "http://127.0.0.1:${API_PORT}/api/bundles" >/dev/null
  echo "API /api/bundles OK."
}

cmd_verify() {
  start_api
  start_portal
  verify_backend
  verify_portal_landing
  echo "Install verification passed (frontend + backend)."
}

cmd_serve() {
  start_api
  start_portal
  echo "Moonshot web UI: http://localhost:${PORTAL_PORT}"
  echo "API: http://localhost:${API_PORT}"
  echo "Press Ctrl+C to stop."
  # Keep container running until signal; cleanup via trap
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

MODE="${1:-verify}"
case "${MODE}" in
  verify) cmd_verify ;;
  serve) cmd_serve ;;
  *)
    echo "usage: $0 [verify|serve]" >&2
    exit 1
    ;;
esac
