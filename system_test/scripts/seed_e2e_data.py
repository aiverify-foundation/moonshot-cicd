#!/usr/bin/env python3
"""
Seed relational data required by Playwright system tests via the running API.

Idempotent: skips providers that already have models/configs and custom apps that
already have configs. Not used by production startup — only E2E (global-setup / run-e2e-tests.sh).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
DEFAULT_CONFIG_NAME = "Default"
CUSTOM_APP_NAME = "API Connector"
CUSTOM_APP_CONFIG_NAME = "Default Configuration"

# Mirror adapter defaults (OpenAIAdapter / TogetherAdapter / CustomApiConnectorAdapter).
PROVIDER_SEEDS = (
    {
        "system_name": "openai_adapter",
        "model_name": "gpt-4o-mini",
        "saved_config_pairs": {"temperature": "1.0"},
    },
    {
        "system_name": "together_adapter",
        "model_name": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "saved_config_pairs": {"temperature": "0.7"},
    },
)
CUSTOM_APP_CONFIG_PAIRS = {
    "api_type": "POST",
    "api_url": "https://api.together.xyz/v1/chat/completions",
    "api_body": (
        '{"model": "meta-llama/Llama-3.3-70B-Instruct-Turbo", '
        '"messages": [{"role": "user", "content": ""}], "max_tokens": 128}'
    ),
}


def _request(method: str, path: str, body: dict | None = None) -> tuple[int, object]:
    url = f"{BASE_URL}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {"detail": exc.reason}
        except json.JSONDecodeError:
            payload = {"detail": raw or exc.reason}
        return exc.code, payload


def _provider_has_models(system_name: str) -> bool:
    encoded = urllib.parse.quote(system_name, safe="")
    status, payload = _request("GET", f"/api/providers/by-system-name/{encoded}/latest-details")
    if status == 404:
        return False
    if status != 200:
        raise RuntimeError(f"latest-details for {system_name!r} failed: HTTP {status} {payload}")
    models = payload.get("models") or []
    db_configs = payload.get("database_model_configs") or []
    return len(models) > 0 or len(db_configs) > 0


def _seed_provider_models() -> None:
    status, providers = _request("GET", "/api/providers")
    if status != 200:
        raise RuntimeError(f"GET /api/providers failed: HTTP {status} {providers}")
    by_system = {p["system_name"]: p for p in providers}

    for seed in PROVIDER_SEEDS:
        system_name = seed["system_name"]
        if _provider_has_models(system_name):
            print(f"E2E seed: skip provider {system_name!r} (models already present)")
            continue
        row = by_system.get(system_name)
        if row is None:
            print(f"E2E seed: skip provider {system_name!r} (not in /api/providers)", file=sys.stderr)
            continue
        provider_id = int(row["id"])
        body = {
            "llm_provider_id": provider_id,
            "model_name": seed["model_name"],
            "name": DEFAULT_CONFIG_NAME,
            "savedConfigPairs": seed["saved_config_pairs"],
        }
        status, payload = _request("POST", "/api/database-model-configs", body)
        if status not in (200, 201):
            raise RuntimeError(
                f"POST /api/database-model-configs for {system_name!r} failed: "
                f"HTTP {status} {payload}"
            )
        print(f"E2E seed: created model config for {system_name!r}")


def _seed_custom_app_config() -> None:
    status, apps = _request("GET", "/api/custom-apps")
    if status != 200:
        raise RuntimeError(f"GET /api/custom-apps failed: HTTP {status} {apps}")
    app = next((a for a in apps if a.get("name") == CUSTOM_APP_NAME), None)
    if app is None:
        print(f"E2E seed: skip custom app {CUSTOM_APP_NAME!r} (not found)", file=sys.stderr)
        return
    app_id = int(app["id"])
    status, configs = _request("GET", f"/api/custom-apps/{app_id}/configs")
    if status != 200:
        raise RuntimeError(f"GET configs for app {app_id} failed: HTTP {status} {configs}")
    if configs:
        print(f"E2E seed: skip custom app {CUSTOM_APP_NAME!r} (configs already present)")
        return
    body = {
        "name": CUSTOM_APP_CONFIG_NAME,
        "savedConfigPairs": CUSTOM_APP_CONFIG_PAIRS,
    }
    status, payload = _request("POST", f"/api/custom-apps/{app_id}/configs", body)
    if status not in (200, 201):
        raise RuntimeError(
            f"POST custom app config for {CUSTOM_APP_NAME!r} failed: HTTP {status} {payload}"
        )
    print(f"E2E seed: created config for {CUSTOM_APP_NAME!r}")


def main() -> int:
    print(f"E2E seed: using API at {BASE_URL}")
    _seed_provider_models()
    _seed_custom_app_config()
    print("E2E seed: done")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"E2E seed failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
