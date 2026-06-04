# Moonshot install-test Docker image

Docker image to validate **frontend + backend** installation and to **host** the Moonshot web UI locally. It mirrors the [Installation Guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki) dev workflow (`poetry install`, `npm install`, `run_api.py`, `npm run dev`) and can run **Playwright system tests** inside the container.

This image is **not** the production CLI image ([`moonshot_core/Dockerfile`](../moonshot_core/Dockerfile)) and does **not** test the `moonshot` CLI.

## Quick start (bootstrap)

Run these from your machine. Replace `/path/to/moonshot-cicd` with your clone path.

**Prerequisites:** Docker is installed and running. Ports **3000** and **8000** are free if you use `serve`.

### Option A — Check that install works (`verify`)

Build the image first if you have not run `serve` or `docker build` yet:

```bash
cd /path/to/moonshot-cicd
docker build -f Dockerfile.install-test -t moonshot-install-test .
```

```bash
cd /path/to/moonshot-cicd
docker run --rm moonshot-install-test
```

You should see `Install verification passed (frontend + backend).`

### Option B — Host Moonshot in your browser (`serve`, persistent data)

`serve` builds the image if it is missing, creates **one Docker named volume**, and starts the stack. Data survives stop/restart and `--rm`.

**Recommended:**

```bash
cd /path/to/moonshot-cicd
./docker/serve.sh
```

First run may take several minutes while the image builds.

**Or manual `docker run`** (same as `serve.sh`; volume `moonshot-install-test-data`):

```bash
cd /path/to/moonshot-cicd
# Build the image (first time, or after code changes)
docker build -f Dockerfile.install-test -t moonshot-install-test .
# Create the persistent data volume (safe to re-run)
docker volume create moonshot-install-test-data
```

```bash
cd /path/to/moonshot-cicd
docker run --rm \
  -p 8000:8000 \
  -p 3000:3000 \
  -v moonshot-install-test-data:/var/lib/moonshot \
  -e MOONSHOT_DB_PATH=/var/lib/moonshot/moonshot_install_test.db \
  -e MOONSHOT_BENCHMARK_RESULTS_DIR=/var/lib/moonshot/results \
  -e MOONSHOT_API_NO_RELOAD=1 \
  moonshot-install-test serve
```

**Or Docker Compose** (one volume `moonshot-data`):

```bash
cd /path/to/moonshot-cicd
docker compose -f docker-compose.install-test.yml up --build
```

Then open **http://localhost:3000** (API at **http://localhost:8000**). Press `Ctrl+C` to stop; run the same command again to resume with the same data.

`./docker/serve.sh` creates or reuses one volume: `moonshot-install-test-data`. In **Docker Desktop**, open **Volumes** and look for that name.

List or remove persisted data:

```bash
docker volume ls | grep moonshot-install-test
docker volume inspect moonshot-install-test-data
docker volume rm moonshot-install-test-data   # wipe DB + results
```

If you still have old two-volume names (`moonshot-install-test-db`, `moonshot-install-test-results`), they are unused after this change; you can remove them with `docker volume rm`.

### Option C — Run E2E tests in Docker (`e2e`)

```bash
cd /path/to/moonshot-cicd
docker run --rm moonshot-install-test e2e
```

### After you change code: rebuild and re-run

```bash
cd /path/to/moonshot-cicd
docker build -f Dockerfile.install-test -t moonshot-install-test .
docker run --rm moonshot-install-test          # verify or e2e
./docker/serve.sh                              # serve (rebuild required after code changes)
```

To force `serve.sh` to skip auto-build (image must already exist): `MOONSHOT_INSTALL_TEST_SKIP_BUILD=1 ./docker/serve.sh`

---

## Requirements

### Host machine

| Requirement | Notes |
|-------------|--------|
| **Docker** | Docker Desktop or Docker Engine 20.10+ with BuildKit |
| **Disk** | ~4–6 GB free for image layers (Python, Node, Chromium, portal build) |
| **RAM** | 4 GB+ recommended for `e2e` (headless Chromium + Next dev) |
| **Network** | Needed for **initial** `docker build` (Poetry/npm/Playwright downloads). Runtime smoke/E2E does not call external LLM APIs |
| **Ports (host mode only)** | **8000** (API) and **3000** (portal dev) must be free when using `serve` |

### Secrets and API keys

| Mode | Secrets required? |
|------|-------------------|
| `verify` | **No** |
| `serve` | **No** for UI exploration. Real benchmark runs from the UI need provider keys configured in Moonshot (DB or env) — not supplied by this image |
| `e2e` | **No**. Tests exercise UI + local API only; see [`system_test/scripts/seed_e2e_data.py`](../system_test/scripts/seed_e2e_data.py) |

`.env` files are excluded from the build context (see [`.dockerignore`](../.dockerignore)). To pass keys at runtime with persistent `serve`:

```bash
OPENAI_API_KEY=sk-... ./docker/serve.sh
# or
docker run --rm ... -e OPENAI_API_KEY -e TOGETHER_API_KEY ... moonshot-install-test serve
```

### Repository layout

Build from the **repo root** (context must include `moonshot_core/`, `moonshot_portal_app/`, `system_test/`, `docker/`).

## Build the image

```bash
cd /path/to/moonshot-cicd
docker build -f Dockerfile.install-test -t moonshot-install-test .
```

First build may take several minutes (Poetry deps, `npm run build`, Playwright Chromium + OS libraries).

## Run modes

Entrypoint: [`install-test-entrypoint.sh`](install-test-entrypoint.sh)

| Mode | Command | Purpose |
|------|---------|---------|
| **verify** (default) | `docker run --rm moonshot-install-test` | Automated install check: starts API + Next dev, HTTP smoke, exits |
| **serve** | `./docker/serve.sh` or `docker compose -f docker-compose.install-test.yml up` | **Host** the app; **named volumes** for DB + results |
| **e2e** | `docker run --rm moonshot-install-test e2e` | Run Playwright system tests (built portal on :8000 only) |

### 1. Verify installation (`verify`)

Matches the Installation Guide **two-server** setup inside the container:

- **Backend:** FastAPI on port **8000** (`python run_api.py`)
- **Frontend:** Next.js dev on port **3000** (`npm run dev`, bound to `0.0.0.0` for Docker)

Checks:

- `GET /api/bundles` on the API
- Landing page HTML on port 3000 (“Run a benchmark test”)

```bash
docker run --rm moonshot-install-test
# equivalent:
docker run --rm moonshot-install-test verify
```

Success ends with: `Install verification passed (frontend + backend).`

### 2. Host / run locally (`serve`)

Use this to **use Moonshot in the browser** the same way as the Installation Guide (portal on 3000, API on 8000).

**Default (persistent):** one Docker volume `moonshot-install-test-data` mounted at `/var/lib/moonshot`:

| Path in volume | Purpose |
|----------------|---------|
| `moonshot_install_test.db` | SQLite (Alembic scripts stay in the image) |
| `results/` | Benchmark result JSON |

Compose uses the same layout via volume `moonshot-data`.

Then open:

- **Web UI:** http://localhost:3000  
- **API:** http://localhost:8000  

Stop with `Ctrl+C` and run `./docker/serve.sh` again — data is kept in the volumes. On startup you should see `Database: /var/lib/moonshot/moonshot_install_test.db` and a growing byte size on the second run.

If data still disappears, check that a repo `.env` does not set `MOONSHOT_DB_PATH` to a path under `/app/moonshot_core/...` (ephemeral inside the container). `serve.sh` forces the volume path **after** loading `.env`.

**Note:** This is a **development-style** stack (hot reload, not production hardening). For production deployment, use the wiki CI/CD and production Docker images.

**Non-persistent `serve` (ephemeral):** `docker run --rm -p 8000:8000 -p 3000:3000 moonshot-install-test serve` (no `-v`; DB lost when the container exits).

### 3. End-to-end tests (`e2e`)

CI-style path: **single server** on **8000** serving the **built** static portal (`moonshot_portal_app/out`), plus Playwright.

```bash
# Full suite (~25 tests, ~1–2 min)
docker run --rm moonshot-install-test e2e

# One file or Playwright flags (optional leading "--")
docker run --rm moonshot-install-test e2e -- tests/model-selection.spec.js
docker run --rm -e CI=false moonshot-install-test e2e   # no retries

# Save reports on the host
docker run --rm \
  -v "$(pwd)/system_test/test-results:/app/system_test/test-results" \
  -v "$(pwd)/system_test/playwright-report:/app/system_test/playwright-report" \
  moonshot-install-test e2e
```

Flow inside the container:

1. Fresh DB: `moonshot_core/data/database/moonshot_e2e.db`
2. Start API on :8000
3. Seed test data via API
4. `npx playwright test` (Chromium headless)

## Environment variables

| Variable | Default | Used in |
|----------|---------|---------|
| `API_PORT` | `8000` | All modes |
| `PORTAL_PORT` | `3000` | `verify`, `serve` |
| `BASE_URL` | `http://localhost:8000` | Waits, E2E, seed (keep **localhost**, not `127.0.0.1`, for browser/API alignment) |
| `INSTALL_TEST_MAX_WAIT` | `90` | Seconds to wait for each service |
| `MOONSHOT_DB_PATH` | `moonshot_install_test.db` (`verify`/`serve`) or `moonshot_e2e.db` (`e2e`) | SQLite path inside container |
| `PYTHONPATH` | `/app/moonshot_core` | Set in image |
| `E2E_PYTHON` | `/app/moonshot-env/bin/python` | `e2e` global setup |
| `CI` | `true` in image | Playwright retries when `true` |

Example:

```bash
docker run --rm -e INSTALL_TEST_MAX_WAIT=120 moonshot-install-test
```

## What gets installed in the image

At **build** time (no manual steps inside the container):

1. Python 3.12 venv at `/app/moonshot-env`
2. `poetry install` in `moonshot_core/`
3. `npm install` in `moonshot_portal_app/`
4. `npm run build` in `moonshot_portal_app/` (static export for `e2e`)
5. `npm install` + Playwright Chromium in `system_test/`

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| Build fails on Poetry | Re-run build; image runs `poetry install` twice (CI workaround) |
| `verify` / `serve` timeout on portal | Increase `INSTALL_TEST_MAX_WAIT`; ensure enough RAM |
| `e2e` failures on bundle/toggle UI | Use `BASE_URL=http://localhost:8000` (default); do not switch to `127.0.0.1` |
| Port already in use | Stop local `run_api.py` / Next dev or change host ports: `-p 8001:8000` (API only helps if the app supports it; portal still expects API on 8000 inside the container) |
| Docker daemon not running | Start Docker Desktop / Engine |
| Lost data after `serve` | Use `./docker/serve.sh` or Compose (named volumes); plain `docker run` without `-v` uses a throwaway DB |
| `Path doesn't exist: .../alembic` on serve | Do not mount over `/app/moonshot_core/data/database/`; use `./docker/serve.sh` (DB on `/var/lib/moonshot` only) |

## Related files

| File | Role |
|------|------|
| [`Dockerfile.install-test`](../Dockerfile.install-test) | Image definition |
| [`.dockerignore`](../.dockerignore) | Build context exclusions |
| [`install-test-entrypoint.sh`](install-test-entrypoint.sh) | `verify` / `serve` / `e2e` logic |
| [`serve.sh`](serve.sh) | Persistent `serve` (default local hosting) |
| [`docker-compose.install-test.yml`](../docker-compose.install-test.yml) | Same as `serve.sh`, via Compose |
| [`run-e2e-tests.sh`](../run-e2e-tests.sh) | Host-native E2E (conda + npm, no Docker) |

## Comparison to manual install

| Installation Guide (host) | Docker |
|---------------------------|--------|
| `python3 -m venv moonshot-env` | Pre-created in image |
| `cd moonshot_core && poetry install` | Done at build |
| `cd moonshot_portal_app && npm install` | Done at build |
| `python run_api.py` + `npm run dev` | `serve` or `verify` |
| Open http://localhost:3000 | `./docker/serve.sh` or Compose |
| `./run-e2e-tests.sh` | `docker run ... e2e` |
