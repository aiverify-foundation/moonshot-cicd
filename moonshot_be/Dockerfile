FROM python:3.12-alpine AS build

WORKDIR /app

# Install build dependencies including Rust
RUN apk update && apk upgrade --no-cache && \
    apk add --no-cache \
    rust \
    cargo \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev

# Copy all code into /app
COPY . .

# Install Poetry and dependencies
RUN pip install poetry==2.1.2 --no-cache-dir && \
    poetry config virtualenvs.create false && \
    poetry install --without process_checks