"""Probe a custom app connector configuration with a live HTTP request."""

from __future__ import annotations

import json
import re
from typing import Dict, List, Tuple

import aiohttp
from jsonpath_ng.ext import parse
from jsonpath_ng.jsonpath import Child, Fields, Index, JSONPath, Root

from application.dto.custom_app_config_dto import (
    ResponseLeafRowDTO,
    TestCustomAppConnectionBody,
    TestCustomAppConnectionResponseDTO,
)
from application.services.custom_app_config_secret_service import (
    CustomAppConfigSecretService,
)
from domain.entities.connector_entity import ConnectorEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

DEFAULT_CONNECTOR_ADAPTER = "custom_api_connector_adapter"
CONNECTION_TEST_PROMPT = "Hase the connection passed ? "

_FIELD_NAME_RE = re.compile(r"^[A-Za-z_@][A-Za-z0-9_@-]*$")


def _format_field_name(name: str, *, with_dot: bool) -> str:
    if _FIELD_NAME_RE.match(name):
        return f".{name}" if with_dot else name
    quoted = f"['{name}']"
    return f".{quoted}" if with_dot else quoted


def _path_segments(path: JSONPath) -> List[Tuple[str, str | int]]:
    if isinstance(path, Child):
        return _path_segments(path.left) + _path_segments(path.right)
    if isinstance(path, Fields):
        return [("field", field) for field in path.fields]
    if isinstance(path, Index):
        return [("index", path.indices[0])]
    if isinstance(path, Root):
        return []
    return []


def _format_jsonpath_leaf_path(path: JSONPath) -> str:
    segments = _path_segments(path)
    if not segments:
        return "$"
    rendered: List[str] = []
    for kind, value in segments:
        if kind == "field":
            rendered.append(_format_field_name(str(value), with_dot=bool(rendered)))
        else:
            rendered.append(f"[{value}]")
    return "".join(rendered)


def _extract_response_leaves(body: str) -> Tuple[bool, List[dict[str, str]]]:
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return False, []
    if not isinstance(data, (dict, list)):
        return True, [{"path": "$", "value": json.dumps(data)}]
    leaves = [
        {
            "path": _format_jsonpath_leaf_path(match.full_path),
            "value": json.dumps(match.value),
        }
        for match in parse("$..*").find(data)
        if not isinstance(match.value, (dict, list))
    ]
    return True, leaves


class CustomAppConnectionTestService:
    def __init__(
        self,
        secret_service: CustomAppConfigSecretService | None = None,
    ) -> None:
        self._secret_service = secret_service or CustomAppConfigSecretService()

    def _resolve_api_key(self, body: TestCustomAppConnectionBody) -> str:
        api_key = (body.api_key or "").strip()
        if api_key:
            return api_key
        if body.config_id is not None and self._secret_service.is_secret_configured(
            body.config_id, "api_key"
        ):
            return self._secret_service.get_decrypted_secret(body.config_id, "api_key")
        raise ValueError(
            "An authorization secret is required to test the connection."
        )

    def _build_connector_entity(
        self, saved_config_pairs: Dict[str, str], api_key: str
    ) -> ConnectorEntity:
        merged = dict(saved_config_pairs)
        adapter_module = (
            merged.pop("connector_adapter", DEFAULT_CONNECTOR_ADAPTER) or ""
        ).strip() or DEFAULT_CONNECTOR_ADAPTER

        try:
            adapter_instance, _ = ModuleLoader.load(adapter_module, ModuleTypes.CONNECTOR)
            adapter_cls = adapter_instance.__class__
            default_pairs: Dict[str, str] = dict(
                getattr(adapter_cls, "DEFAULT_CONFIG_PAIRS", {})
            )
        except Exception as exc:
            logger.error("Failed to load connector adapter %s: %s", adapter_module, exc)
            raise ValueError(
                f"Failed to load connector adapter {adapter_module!r}"
            ) from exc

        params = {**default_pairs, **merged, "api_key": api_key}
        model_endpoint = str(params.pop("base_url", "") or "").strip()

        return ConnectorEntity(
            connector_adapter=adapter_module,
            model="",
            model_endpoint=model_endpoint,
            params=params,
        )

    async def test_connection(
        self, body: TestCustomAppConnectionBody
    ) -> TestCustomAppConnectionResponseDTO:
        api_key = self._resolve_api_key(body)
        entity = self._build_connector_entity(body.savedConfigPairs, api_key)

        try:
            adapter_instance, _ = ModuleLoader.load(
                entity.connector_adapter, ModuleTypes.CONNECTOR
            )
        except Exception as exc:
            logger.error(
                "Failed to load connector adapter %s: %s",
                entity.connector_adapter,
                exc,
            )
            return TestCustomAppConnectionResponseDTO(
                success=False,
                error=f"Failed to load connector adapter {entity.connector_adapter!r}",
            )

        adapter: ConnectorPort = adapter_instance
        try:
            adapter.configure(entity)
        except ValueError as exc:
            return TestCustomAppConnectionResponseDTO(success=False, error=str(exc))

        if not hasattr(adapter, "probe"):
            return TestCustomAppConnectionResponseDTO(
                success=False,
                error="Connector adapter does not support connection probing.",
            )

        try:
            status_code, response_body = await adapter.probe(CONNECTION_TEST_PROMPT)
        except aiohttp.ClientError as exc:
            return TestCustomAppConnectionResponseDTO(
                success=False,
                error=f"Connection failed: {exc}",
            )
        except Exception as exc:
            logger.error("Custom app connection test failed: %s", exc)
            return TestCustomAppConnectionResponseDTO(
                success=False,
                error=str(exc),
            )

        success = 200 <= status_code < 300
        error = None if success else f"HTTP {status_code}"
        response_is_json, leaf_rows = _extract_response_leaves(response_body)
        return TestCustomAppConnectionResponseDTO(
            success=success,
            status_code=status_code,
            response_body=response_body,
            error=error,
            response_is_json=response_is_json,
            response_leaves=[ResponseLeafRowDTO(**row) for row in leaf_rows],
        )
