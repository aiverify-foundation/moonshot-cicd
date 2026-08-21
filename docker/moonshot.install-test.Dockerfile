# Install-test image: Installation Guide (verify/serve) + Playwright E2E (e2e mode).
#
#   docker build -f docker/moonshot.install-test.Dockerfile -t moonshot-install-test .
#   docker run --rm moonshot-install-test                    # install smoke (dev :3000 + API :8000)
#   ./docker/serve.sh   OR   docker compose -f docker/moonshot.install-test.docker-compose.yml up
#   docker run --rm moonshot-install-test e2e                # Playwright (built portal on :8000)
#   docker run --rm moonshot-install-test e2e -- tests/model-selection.spec.js
#   docker run --rm -v "$(pwd)/system_test/test-results:/app/system_test/test-results" moonshot-install-test e2e

FROM node:22-bookworm AS node_base

FROM python:3.12-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=node_base /usr/local/bin/node /usr/local/bin/node
COPY --from=node_base /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

WORKDIR /app

RUN python3 -m venv /app/moonshot-env
ENV PATH="/app/moonshot-env/bin:${PATH}"
ENV VIRTUAL_ENV=/app/moonshot-env
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/moonshot_core
# MOONSHOT_DB_PATH is set at runtime (serve: volume; verify/e2e: entrypoint)
# Must match moonshot_portal_app/lib/api.ts (localhost:8000) for same-origin fetches in Playwright
ENV BASE_URL=http://localhost:8000
ENV E2E_PYTHON=/app/moonshot-env/bin/python
ENV CI=true

COPY moonshot_core /app/moonshot_core
COPY moonshot_portal_app /app/moonshot_portal_app
COPY system_test /app/system_test

RUN mkdir -p /app/moonshot_core/data/database

WORKDIR /app/moonshot_core
RUN pip install --upgrade pip && pip install poetry==2.1.2 --no-cache-dir \
    && (set +e; poetry install; set -e; poetry install)

# Portal: deps + static export for E2E (API serves moonshot_portal_app/out on :8000)
WORKDIR /app/moonshot_portal_app
RUN npm install && npm run build

# Playwright system tests (Chromium + OS libraries for headless browser)
WORKDIR /app/system_test
RUN npm install \
    && npx playwright install chromium \
    && npx playwright install-deps chromium

COPY scripts/install-test-entrypoint.sh /app/scripts/install-test-entrypoint.sh
RUN chmod +x /app/scripts/install-test-entrypoint.sh

WORKDIR /app

ENTRYPOINT ["/app/scripts/install-test-entrypoint.sh"]
CMD ["verify"]
