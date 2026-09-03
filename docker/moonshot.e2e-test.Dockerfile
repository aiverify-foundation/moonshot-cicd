# Playwright E2E runner: system_test + moonshot_core (seed scripts / PYTHONPATH).
# Build from repo root:
#   docker build -f docker/moonshot.e2e-test.Dockerfile -t moonshot-e2e-test .
#
# Run against a Moonshot web instance (BASE_URL):
#   docker run --rm -e BASE_URL=http://host.docker.internal:8000 -e CI=1 moonshot-e2e-test

FROM mcr.microsoft.com/playwright:v1.56.0-noble

ENV \
    POETRY_VIRTUALENVS_CREATE=false \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH=/app/moonshot_core \
    E2E_PYTHON=/app/.venv/bin/python \
    CI=1

WORKDIR /app

RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/bin/python3 /usr/local/bin/python \ 
    mkdir -p /var/lib/moonshot

COPY moonshot_core/ /app/moonshot_core/
COPY system_test/ /app/system_test/

RUN python3 -m venv /app/.venv && \
    pip install --no-cache-dir poetry==2.4.1

WORKDIR /app/moonshot_core
RUN poetry install --only main

WORKDIR /app/system_test
RUN npm ci && npx playwright install --with-deps chromium

CMD ["npm", "run", "test"]
