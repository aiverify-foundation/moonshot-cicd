"""Centralized feature flags for optional product capabilities."""

from __future__ import annotations

OPENROUTER_ADAPTER_SYSTEM_NAME = "openrouter_adapter"

# Flip to False to disable the OpenRouter provider.
ENABLE_OPENROUTER = True


def is_openrouter_enabled() -> bool:
    """Whether the OpenRouter provider is enabled via ``ENABLE_OPENROUTER``."""
    return ENABLE_OPENROUTER
