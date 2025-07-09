FROM python:3.12-alpine AS build

WORKDIR /app

# patches and dependencies
RUN apk update && apk upgrade --no-cache

# Copy all code into /app
COPY . .

# Install Poetry and dependencies
RUN pip install poetry==2.1.2 --no-cache-dir && \
    poetry config virtualenvs.create false && \
    poetry install --without process_checks