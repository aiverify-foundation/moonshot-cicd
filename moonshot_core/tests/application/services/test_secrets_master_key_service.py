"""Tests for SecretsMasterKeyService."""

from __future__ import annotations

import base64
from unittest.mock import MagicMock

import pytest

from application.services.secrets_master_key_service import SecretsMasterKeyService
from domain.entities.moonshot_config_entity import MoonshotConfigEntity
from domain.services.secret_encryption import MOONSHOT_SECRETS_MASTER_KEY_CONFIG_KEY


@pytest.fixture
def mock_config() -> MagicMock:
    return MagicMock()


def test_creates_and_persists_master_key(mock_config):
    mock_config.get_by_key.return_value = None
    mock_config.set.return_value = MagicMock()
    svc = SecretsMasterKeyService(mock_config)
    key = svc.get_or_create_master_key_bytes()
    assert len(key) == 32
    mock_config.set.assert_called_once()
    call_kw = mock_config.set.call_args[0]
    assert call_kw[0] == MOONSHOT_SECRETS_MASTER_KEY_CONFIG_KEY
    stored_b64 = call_kw[1]
    assert base64.b64decode(stored_b64.encode("ascii")) == key


def test_loads_existing_master_key(mock_config):
    raw = b"z" * 32
    b64 = base64.b64encode(raw).decode("ascii")
    mock_config.get_by_key.return_value = MoonshotConfigEntity(id=1, key="k", value=b64)
    svc = SecretsMasterKeyService(mock_config)
    assert svc.get_or_create_master_key_bytes() == raw
    mock_config.set.assert_not_called()


def test_invalid_stored_length_raises(mock_config):
    mock_config.get_by_key.return_value = MoonshotConfigEntity(
        id=1, key="k", value=base64.b64encode(b"short").decode("ascii")
    )
    svc = SecretsMasterKeyService(mock_config)
    with pytest.raises(ValueError, match="32 bytes"):
        svc.get_or_create_master_key_bytes()
