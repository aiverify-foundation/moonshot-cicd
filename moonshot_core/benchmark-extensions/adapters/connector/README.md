# Custom connector adapters

Place connector modules here as `<name>_adapter.py` (for example `my_api_adapter.py`).

Register each connector in the extension `moonshot_config.yaml` under `connectors_configurations` with a unique `id`. Extension connector ids must not duplicate built-in connector ids from the shipped config.

For implementation patterns, see the in-repo reference adapter at `moonshot_core/src/adapters/connector/together_adapter.py` (`SYSTEM_NAME`, `VERSION`, `PROVIDER_NAME`, and the connector port interface).
