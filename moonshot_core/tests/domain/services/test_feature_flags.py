"""Tests for centralized feature flags."""

from domain.services import feature_flags
from domain.services.feature_flags import is_openrouter_enabled


def test_is_openrouter_enabled_when_constant_false(monkeypatch):
    monkeypatch.setattr(feature_flags, "ENABLE_OPENROUTER", False)
    assert is_openrouter_enabled() is False


def test_is_openrouter_enabled_when_constant_true(monkeypatch):
    monkeypatch.setattr(feature_flags, "ENABLE_OPENROUTER", True)
    assert is_openrouter_enabled() is True
