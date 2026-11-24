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

**Restart after any change.** The overlay `moonshot_config.yaml`, the feature flag and the decision about whether the overlay is valid are read once per API process. Restart the API after you edit anything in the extensions directory. `POST /api/seed-shared-config-if-changed` re-reads only the overlay `shared.yaml`, so do not rely on it to apply other overlay changes.

## Invalid overlays are ignored

If the overlay cannot be used, the API ignores **the whole overlay** and runs on the built-in benchmarks, datasets, adapters and config. It logs an error that names the reason, and it does not exit. The overlay is checked again on the next restart. An overlay is ignored when:

- `moonshot_config.yaml` or `test_configs/shared.yaml` is malformed or unreadable.
- A connector id, metric name, attack module name, `common` key or bundle key duplicates a built-in one.
- A dataset id (the file name without `.json`) in `datasets/` duplicates a built-in dataset.
- A test has no `dataset` or no `metric.name`.
- A test names a dataset that is in neither `datasets/` nor the built-in `data/datasets/`.

Not checked at startup: Python errors inside an adapter (they appear when a run loads it), a metric used by a bundle but missing from the `metrics:` section of `moonshot_config.yaml`.

**Adapter name collisions:** an adapter file whose name matches a built-in adapter does not replace it. The built-in adapter is used, the extension file is ignored, and an error is logged at startup and on first load. The rest of the overlay stays active. Rename the file to use it.

## Local development

Set `MOONSHOT_BENCHMARK_EXTENSIONS_DIR` to this folder so the API loads it. There is no fallback to `moonshot_core/benchmark-extensions.example/` when the variable is unset.

```bash
export MOONSHOT_BENCHMARK_EXTENSIONS_DIR="$PWD/benchmark-extensions.example"   # from moonshot_core/
python run_api.py
```

## Docker

Compose does not set `MOONSHOT_BENCHMARK_EXTENSIONS_DIR`. When the variable is unset, the app uses `/var/lib/moonshot/benchmark-extensions` on the data volume if that directory exists. If it does not exist, no overlay is loaded. The copy baked into the image is not used.

**You** populate that path on the persistent volume (or bind-mount a host directory there) using the layout above.

1. Place extension files under `/var/lib/moonshot/benchmark-extensions/` on the data volume.
2. Enable **`AIVET_OCT2026_MOON807=true`** in `feature_flags.txt` and rebuild/restart the image if needed.
3. Restart `moonshot-web` or call `POST /api/seed-shared-config-if-changed` so bundle changes seed into the DB.

Example bind-mount in `docker/moonshot.docker-compose.yml`:

```yaml
volumes:
  - moonshot-cicd-data-volume:/var/lib/moonshot
  - ./moonshot_core/benchmark-extensions.example:/var/lib/moonshot/benchmark-extensions:ro
```

(Only if you keep extensions on the host; production setups typically manage the volume directly.)
