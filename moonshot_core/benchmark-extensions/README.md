# Benchmark extensions (example)

Copy this directory layout into your extensions root and customize. Built-in benchmarks in the Docker image stay unchanged; your files are **merged** on top.

## Layout

| Path | Purpose |
|------|---------|
| `moonshot_config.yaml` | Optional fragment: extra `connectors_configurations`, `metrics`, `attack_modules` |
| `test_configs/shared.yaml` | Optional fragment: new bundle keys only |
| `datasets/<id>.json` | Dataset files referenced by `shared.yaml` (`dataset: <id>`) |
| `adapters/metric/<name>.py` | Custom metric adapters |
| `adapters/connector/<name>.py` | Custom connector adapters |

Duplicate IDs/names that already exist in the shipped product are rejected at startup or seed time.

Extensions are applied only when feature flag **`AIVET_OCT2026_MOON807=true`** in `moonshot_core/data/feature_flags.txt` (restart the API after changing flags).

## Local development

With the API run from `moonshot_core/`, create `benchmark-extensions/` next to `moonshot_config.yaml`. If `MOONSHOT_BENCHMARK_EXTENSIONS_DIR` is unset, the app uses that folder when it exists.

## Docker

Compose sets `MOONSHOT_BENCHMARK_EXTENSIONS_DIR=/var/lib/moonshot/benchmark-extensions`. **You** populate that path on the persistent volume (or bind-mount a host directory there) using the layout above—copy files, your own automation, or a volume mount in compose.

1. Place extension files under `/var/lib/moonshot/benchmark-extensions/` on the data volume.
2. Enable **`AIVET_OCT2026_MOON807=true`** in `feature_flags.txt` and rebuild/restart the image if needed.
3. Restart `moonshot-web` or call `POST /api/seed-shared-config-if-changed` so bundle changes seed into the DB.

Example bind-mount in `docker/moonshot.docker-compose.yml`:

```yaml
volumes:
  - moonshot-cicd-data-volume:/var/lib/moonshot
  - ./moonshot_core/benchmark-extensions:/var/lib/moonshot/benchmark-extensions:ro
```

(Only if you keep extensions on the host; production setups typically manage the volume directly.)
