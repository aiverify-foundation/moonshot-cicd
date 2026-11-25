"""Provider definitions for benchmark-extension connectors, read from ``providers.json``.

The file lives next to the extension connector adapters::

    <extensions dir>/adapters/connector/providers.json

It lets an extension connector appear as an LLM provider in the portal. Each entry has the
same shape as ``ConnectorPort.provider_seed_definition()`` plus ``adapter_module``, the
connector module (file name without ``.py``) that runs the provider.

The service also records which providers came from an extension, so they can be hidden from
the portal when the overlay is not active (``llm_provider`` rows are never deleted).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from application.ports.moonshot_config_repository import MoonshotConfigRepository
from domain.services.benchmark_extensions import (
    extensions_adapter_dir,
    resolve_extensions_dir,
)
from domain.services.enums.module_types import ModuleTypes
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

PROVIDERS_FILE_NAME = "providers.json"
EXTENSION_PROVIDER_SYSTEM_NAMES_KEY = "extension_provider_system_names"

# Adapter modules are loaded by file name from the extensions adapters directory, so only a
# plain module name is accepted (no path separators or dots).
_ADAPTER_MODULE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Keys passed to the provider seed. ``adapter_module`` is used only for running the provider.
_SEED_KEYS = (
    "name",
    "system_name",
    "version",
    "defaultModel",
    "modelTextboxExplanation",
    "defaultConfigPairs",
)


def _builtin_system_names() -> set[str]:
    """
    System names an extension provider must not reuse.

    Imports are local: ``database_connector_config_service`` imports this module, so a
    top-level import would be circular.
    """
    from adapters.connector.aws_bedrock_adapter import AWSBedrockAdapter
    from adapters.connector.bedrock_mantle_web_search_adapter import (
        BedrockMantleWebSearchAdapter,
    )
    from adapters.connector.openai_adapter import OpenAIAdapter
    from adapters.connector.openrouter_adapter import OpenRouterAdapter
    from adapters.connector.together_adapter import TogetherAdapter
    from application.services.database_connector_config_service import (
        SYSTEM_NAME_TO_ADAPTER_MODULE,
    )

    names = set(SYSTEM_NAME_TO_ADAPTER_MODULE)
    names.update(
        adapter.SYSTEM_NAME
        for adapter in (
            OpenAIAdapter,
            TogetherAdapter,
            OpenRouterAdapter,
            AWSBedrockAdapter,
            BedrockMantleWebSearchAdapter,
        )
    )
    return names


class ExtensionProviderService:
    """Read extension provider definitions and track which providers they created."""

    # Parsed definitions, shared by all instances. The key is the resolved extensions
    # directory (``None`` when extensions are not in use), so a change in whether the overlay
    # is active is picked up. The file is read once per process; restart after editing it.
    _cache: Optional[tuple[Optional[Path], list[dict[str, Any]]]] = None

    def __init__(self, config_repository: Optional[MoonshotConfigRepository] = None) -> None:
        self._config_repository = config_repository

    @classmethod
    def reset(cls) -> None:
        """Forget the cached definitions (for tests; production re-reads on restart)."""
        cls._cache = None

    # ------------------------------------------------------------------ definitions

    def load_definitions(self) -> list[dict[str, Any]]:
        """
        Return the validated extension provider definitions, or ``[]``.

        Empty when extensions are not in use (flag off, no directory, or an invalid overlay)
        or when there is no ``providers.json``. A bad file or entry is logged and skipped. It
        does not invalidate the rest of the overlay.
        """
        extensions_dir = resolve_extensions_dir()
        cached = type(self)._cache
        if cached is not None and cached[0] == extensions_dir:
            return [dict(d) for d in cached[1]]

        definitions = self._read_definitions(extensions_dir) if extensions_dir is not None else []
        type(self)._cache = (extensions_dir, definitions)
        return [dict(d) for d in definitions]

    def load_seed_definitions(self) -> list[dict[str, Any]]:
        """Return the definitions with only the keys the provider seed uses."""
        return [{key: definition[key] for key in _SEED_KEYS} for definition in self.load_definitions()]

    def get_adapter_module(self, system_name: str) -> Optional[str]:
        """Return the connector module for an extension provider, or ``None``."""
        definition = self._find(system_name)
        return definition["adapter_module"] if definition else None

    def get_seed_defaults(self, system_name: str) -> Optional[dict[str, Any]]:
        """Return the seed fields (default model, help text, default config) for a provider."""
        definition = self._find(system_name)
        if definition is None:
            return None
        return {key: definition[key] for key in _SEED_KEYS}

    def _find(self, system_name: str) -> Optional[dict[str, Any]]:
        for definition in self.load_definitions():
            if definition["system_name"] == system_name:
                return definition
        return None

    @staticmethod
    def providers_file_path(extensions_dir: Path) -> Path:
        return extensions_adapter_dir(extensions_dir, ModuleTypes.CONNECTOR) / PROVIDERS_FILE_NAME

    def _read_definitions(self, extensions_dir: Path) -> list[dict[str, Any]]:
        path = self.providers_file_path(extensions_dir)
        if not path.is_file():
            return []
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, UnicodeError, ValueError) as exc:
            logger.error("Ignoring extension providers file %s: could not read it: %s", path, exc)
            return []

        entries = data.get("providers") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            logger.error(
                "Ignoring extension providers file %s: expected an object with a 'providers' list",
                path,
            )
            return []

        builtin_names = _builtin_system_names()
        seen: set[str] = set()
        definitions: list[dict[str, Any]] = []
        for index, entry in enumerate(entries):
            definition, error = self._validate_entry(entry, builtin_names, seen)
            if definition is None:
                logger.error("Skipping extension provider #%d in %s: %s", index, path, error)
                continue
            seen.add(definition["system_name"])
            definitions.append(definition)
        if definitions:
            logger.info("Loaded %d extension provider(s) from %s", len(definitions), path)
        return definitions

    @staticmethod
    def _validate_entry(
        entry: Any, builtin_names: set[str], seen: set[str]
    ) -> tuple[Optional[dict[str, Any]], str]:
        """Return ``(definition, "")`` for a valid entry, else ``(None, reason)``."""
        if not isinstance(entry, dict):
            return None, "entry must be an object"

        for key in ("name", "system_name", "adapter_module"):
            value = entry.get(key)
            if not isinstance(value, str) or not value.strip():
                return None, f"'{key}' must be a non-empty string"

        version = entry.get("version")
        if isinstance(version, bool) or not isinstance(version, int):
            return None, "'version' must be an integer"

        name = entry["name"].strip()
        system_name = entry["system_name"].strip()
        adapter_module = entry["adapter_module"].strip()

        if not _ADAPTER_MODULE_PATTERN.match(adapter_module):
            return None, f"'adapter_module' {adapter_module!r} must be a plain module name"
        if system_name in builtin_names:
            return None, f"'system_name' {system_name!r} duplicates a built-in provider"
        if system_name in seen:
            return None, f"'system_name' {system_name!r} is listed more than once"

        text_values: dict[str, str] = {}
        for key in ("defaultModel", "modelTextboxExplanation"):
            value = entry.get(key, "")
            if not isinstance(value, str):
                return None, f"'{key}' must be a string"
            text_values[key] = value

        pairs = entry.get("defaultConfigPairs", {})
        if not isinstance(pairs, dict):
            return None, "'defaultConfigPairs' must be an object"

        return (
            {
                "name": name,
                "system_name": system_name,
                "version": version,
                "adapter_module": adapter_module,
                "defaultModel": text_values["defaultModel"],
                "modelTextboxExplanation": text_values["modelTextboxExplanation"],
                "defaultConfigPairs": {str(k): str(v) for k, v in pairs.items()},
            },
            "",
        )

    # ------------------------------------------------------------------ visibility

    def _repository(self) -> MoonshotConfigRepository:
        if self._config_repository is None:
            from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import (
                MoonshotConfigAdapter,
            )

            self._config_repository = MoonshotConfigAdapter()
        return self._config_repository

    def _recorded_system_names(self) -> set[str]:
        entity = self._repository().get_by_key(EXTENSION_PROVIDER_SYSTEM_NAMES_KEY)
        if entity is None or not (entity.value or "").strip():
            return set()
        try:
            data = json.loads(entity.value)
        except ValueError:
            logger.warning("Ignoring malformed %s in moonshot_config", EXTENSION_PROVIDER_SYSTEM_NAMES_KEY)
            return set()
        if not isinstance(data, list):
            return set()
        return {str(item) for item in data}

    def record_seeded_system_names(self, system_names: list[str]) -> None:
        """
        Remember that these providers came from an extension.

        The stored list is the union of what was stored and ``system_names``, so it only grows
        and a name is not forgotten once its entry leaves ``providers.json``.
        """
        if not system_names:
            return
        recorded = self._recorded_system_names()
        merged = recorded | set(system_names)
        if merged == recorded:
            return
        self._repository().set(EXTENSION_PROVIDER_SYSTEM_NAMES_KEY, json.dumps(sorted(merged)))

    def hidden_system_names(self) -> set[str]:
        """
        System names of extension providers that should not be shown in the portal.

        These are the recorded extension providers that are not in the currently active
        definitions. All of them are hidden when the overlay is off or invalid.
        """
        try:
            recorded = self._recorded_system_names()
        except Exception as exc:  # noqa: BLE001 - a lookup failure must not break provider listing
            logger.warning("Could not read recorded extension providers: %s", exc)
            return set()
        if not recorded:
            return set()
        active = {definition["system_name"] for definition in self.load_definitions()}
        return recorded - active
