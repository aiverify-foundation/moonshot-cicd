#!/usr/bin/env python3
"""
Clear llm_provider_api_key rows for a provider system_name (E2E only).

Used by Playwright beforeEach hooks that assert Token* / no-saved-key UX.

Usage:
  MOONSHOT_DB_PATH=... PYTHONPATH=moonshot_core \\
    python system_test/scripts/clear_provider_api_key.py openai_adapter
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MOONSHOT_CORE_ROOT = REPO_ROOT / "moonshot_core"
SRC_PATH = MOONSHOT_CORE_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from adapters.driven.repository.sqlalchemy.llm_provider_models import (  # noqa: E402
    LLMProviderApiKeyModel,
    LLMProviderModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import (  # noqa: E402
    SessionManager,
)


def clear_provider_api_key(system_name: str) -> int:
    """Delete all API key rows for the given provider system_name. Returns rows deleted."""
    SessionManager.reset_instance()
    session_manager = SessionManager.get_instance()
    with session_manager.get_session() as session:
        provider = (
            session.query(LLMProviderModel)
            .filter(LLMProviderModel.system_name == system_name)
            .first()
        )
        if provider is None:
            raise RuntimeError(f"No llm_provider with system_name={system_name!r}")
        deleted = (
            session.query(LLMProviderApiKeyModel)
            .filter(LLMProviderApiKeyModel.llm_provider_id == provider.id)
            .delete(synchronize_session=False)
        )
        return int(deleted or 0)


def main() -> int:
    system_name = sys.argv[1] if len(sys.argv) > 1 else "openai_adapter"
    try:
        deleted = clear_provider_api_key(system_name)
    except Exception as exc:
        print(f"error: clear API key failed: {exc}", file=sys.stderr)
        return 1
    print(f"E2E clear: removed {deleted} api key row(s) for {system_name!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
