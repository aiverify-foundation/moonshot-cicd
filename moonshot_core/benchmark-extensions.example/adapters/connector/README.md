# Custom connector adapters

Place connector modules here as `<name>_adapter.py`.

The working example is `benchmark_extension_openai_adapter.py` (`BenchmarkExtensionOpenAIAdapter`). It is registered in the extension `moonshot_config.yaml` as connector id `benchmark-extension-openai`.

Register each connector under `connectors_configurations` with a unique `id`. Extension connector ids must not duplicate built-in connector ids from the shipped config.

Class attributes follow the in-repo adapters: `SYSTEM_NAME`, `VERSION`, and `PROVIDER_NAME` (see `moonshot_core/src/adapters/connector/together_adapter.py`).

## Showing a connector as a portal provider

Add `providers.json` in this folder. The example file lists `BenchmarkExtensionOpenAIAdapter`:

```json
{
  "providers": [
    {
      "name": "Benchmark Extension OpenAI",
      "system_name": "benchmark_extension_openai_adapter",
      "version": 1,
      "adapter_module": "benchmark_extension_openai_adapter",
      "defaultModel": "gpt-4o-mini",
      "modelTextboxExplanation": "Enter an OpenAI model name, e.g. gpt-4o-mini",
      "defaultConfigPairs": { "temperature": "1.0" }
    }
  ]
}
```

- `system_name` must be unique and must not be a built-in provider (`openai_adapter`, `together_ai`, and so on).
- `adapter_module` is the connector file name without `.py`.
- `version` is an int. Bump it to add a new provider row after you change the entry. A lower or equal version does nothing.
- The file is read at startup. Restart the API after you change it.
- The provider only appears in the portal while the overlay is active (`AIVET_OCT2026_MOON807=true` and a valid extensions directory). Removing the entry, or turning the overlay off, hides it again. The row is kept in the database.
