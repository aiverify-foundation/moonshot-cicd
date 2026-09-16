# Docker images

Production images for Moonshot (CLI + web UI) and Process Checks.

## Moonshot (portal + API)

Builds the portal static export into the Python image and runs `moonshot-web` on port **8000**.

**Compose (recommended):**

```bash
cd /path/to/moonshot-cicd
docker compose -f docker/moonshot.docker-compose.yml up --build
```

Then open **http://localhost:8000**. Data persists in the named volume `moonshot-cicd-data-volume`.

**Manual build/run:**

```bash
cd /path/to/moonshot-cicd
docker build -f docker/moonshot.Dockerfile -t moonshot-cicd .
docker volume create moonshot-cicd-data-volume
docker run --rm \
  -p 8000:8000 \
  -v moonshot-cicd-data-volume:/var/lib/moonshot \
  -e MOONSHOT_DB_PATH=/var/lib/moonshot/moonshot.db \
  -e MOONSHOT_BENCHMARK_RESULTS_DIR=/var/lib/moonshot/results \
  -e MOONSHOT_API_NO_RELOAD=1 \
  moonshot-cicd moonshot-web
```

## Process Checks

Streamlit app image. Build from the `process_check_app` directory:

```bash
cd /path/to/moonshot-cicd
docker build -f docker/process-check-app.Dockerfile -t process-check-app process_check_app
docker run --rm -p 8501:8501 process-check-app
```

Open **http://localhost:8501**.

## E2E tests

Playwright system tests run on the host (not via Docker):

```bash
./scripts/run-e2e-tests.sh
```

## Related files

| File | Role |
|------|------|
| [`moonshot.Dockerfile`](moonshot.Dockerfile) | Moonshot CLI + static portal |
| [`moonshot.docker-compose.yml`](moonshot.docker-compose.yml) | Local Moonshot web with persistent volume |
| [`process-check-app.Dockerfile`](process-check-app.Dockerfile) | Process Checks Streamlit image |
| [`../scripts/run-e2e-tests.sh`](../scripts/run-e2e-tests.sh) | Host-native Playwright E2E |
