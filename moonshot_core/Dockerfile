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
    cargo=1.87.0-r0 

# Copy all code into /app
COPY . .

# Install Poetry and dependencies
RUN chown -R appuser:appgroup /app && \
    pip install poetry==2.1.2 --no-cache-dir && \
    poetry config virtualenvs.create false && \
    poetry install

# Switch to the non-root user
USER appuser
