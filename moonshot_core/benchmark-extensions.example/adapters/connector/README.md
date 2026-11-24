# Custom connector adapters

Place connector modules here as `<name>_adapter.py`.

The working example is `benchmark_extension_openai_adapter.py` (`BenchmarkExtensionOpenAIAdapter`). It is registered in the extension `moonshot_config.yaml` as connector id `benchmark-extension-openai`.

Register each connector under `connectors_configurations` with a unique `id`. Extension connector ids must not duplicate built-in connector ids from the shipped config.

Class attributes follow the in-repo adapters: `SYSTEM_NAME`, `VERSION`, and `PROVIDER_NAME` (see `moonshot_core/src/adapters/connector/together_adapter.py`).
