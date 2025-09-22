FROM python:3.12-alpine AS build

WORKDIR /app

# Create a non-root user and group.
# -S: Create a system user/group (no password, no home directory by default)
# -u 1001: Assign a specific UID (e.g., 1001) for consistency
# -G appgroup: Add the user to the 'appgroup'
RUN addgroup -S appgroup && adduser -S -u 1001 -G appgroup appuser

# Install build dependencies including Rust
RUN apk update && apk upgrade --no-cache && \
    apk add --no-cache \
    rust=1.87.0-r0 \
    cargo=1.87.0-r0 \
    gcc=14.2.0-r6 \
    musl-dev=1.2.5-r10 \
    libffi-dev=3.4.8-r0 \
    openssl-dev=3.5.2-r0

# Copy all code into /app
COPY . .

# Install Poetry and dependencies
RUN chown -R appuser:appgroup /app && \
    pip install poetry==2.1.2 --no-cache-dir && \
    poetry config virtualenvs.create false && \
    poetry install

# Switch to the non-root user
USER appuser
