# Build portal static export (discarded after COPY into final stage)
FROM node:22-bookworm AS frontend

# Generator + SoT for npm run build (package.json prefixes generate_feature_flags.py)
COPY scripts/generate_feature_flags.py /scripts/generate_feature_flags.py
COPY moonshot_core/data/feature_flags.txt /flags/feature_flags.txt
COPY moonshot_portal_app/ /portal/

ENV FEATURE_FLAGS_TXT=/flags/feature_flags.txt \
    FEATURE_FLAGS_PY_OUT=/tmp/feature_flag_names.py \
    FEATURE_FLAGS_TS_OUT=/portal/lib/featureFlags.ts

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /portal
RUN npm install && npm run build

# Final runtime image: Python only + static HTML
FROM python:3.12-slim-bookworm AS build


ENV \
    # Allow poerty to create /app/.venv and add .venv/bin to PATH 
    # so moonshot & moonshot-web is callable from the CLI instead of "poetry run moonshot"
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:${PATH}" \
    # Override moonshot_config.yaml frontend_build_directory for this image layout
    MOONSHOT_FRONTEND_BUILD_DIRECTORY=/app/data/web

WORKDIR /app

# Upgrade system packages
RUN apt-get update && apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and group and .
RUN groupadd --system appgroup && \
    useradd --system --uid 1001 --gid appgroup appuser

# Moonshot core contents live at /app (build from repo root)
COPY --chown=appuser:appgroup moonshot_core/ /app/

# Copy web Static export from frontend stage
COPY --chown=appuser:appgroup --from=frontend /portal/out/ /app/data/web/

# Install Poetry + project (root install is required for moonshot / moonshot-web scripts)
RUN mkdir -p /app/data/database && \
    mkdir -p /var/lib/moonshot && \
    chown -R appuser:appgroup /var/lib/moonshot && \
    pip install poetry==2.4.1 --no-cache-dir && \
    poetry install --only main

# Switch to the non-root user
USER appuser
EXPOSE 8000
