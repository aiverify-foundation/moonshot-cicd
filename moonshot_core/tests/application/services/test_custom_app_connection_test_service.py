import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.dto.custom_app_config_dto import TestCustomAppConnectionBody
from application.services.custom_app_connection_test_service import (
    CONNECTION_TEST_PROMPT,
    CustomAppConnectionTestService,
)


@pytest.mark.asyncio
async def test_test_connection_uses_form_api_key():
    secret_service = MagicMock()
    secret_service.is_secret_configured.return_value = False

    mock_adapter = MagicMock()
    mock_adapter.probe = AsyncMock(
        return_value=(
            200,
            '{"choices":[{"message":{"content":"yes"}}]}',
        )
    )

    body = TestCustomAppConnectionBody(
        savedConfigPairs={
            "connector_adapter": "custom_api_connector_adapter",
            "api_type": "POST",
            "api_url": "https://api.example.com",
            "api_body": json.dumps(
                {"messages": [{"role": "user", "content": "{{prompt}}"}]}
            ),
        },
        api_key="sk-test",
    )

    with patch(
        "application.services.custom_app_connection_test_service.ModuleLoader.load",
        return_value=(mock_adapter, None),
    ):
        service = CustomAppConnectionTestService(secret_service=secret_service)
        result = await service.test_connection(body)

    assert result.success is True
    assert result.status_code == 200
    assert result.response_body == '{"choices":[{"message":{"content":"yes"}}]}'
    assert result.response_is_json is True
    assert len(result.response_leaves) == 1
    assert result.response_leaves[0].path == "choices[0].message.content"
    assert result.response_leaves[0].value == '"yes"'
    mock_adapter.configure.assert_called_once()
    mock_adapter.probe.assert_awaited_once_with(CONNECTION_TEST_PROMPT)
    secret_service.get_decrypted_secret.assert_not_called()


@pytest.mark.asyncio
async def test_test_connection_uses_stored_secret_when_config_id_provided():
    secret_service = MagicMock()
    secret_service.is_secret_configured.return_value = True
    secret_service.get_decrypted_secret.return_value = "stored-secret"

    mock_adapter = MagicMock()
    mock_adapter.probe = AsyncMock(return_value=(401, "unauthorized"))

    body = TestCustomAppConnectionBody(
        savedConfigPairs={
            "connector_adapter": "custom_api_connector_adapter",
            "api_type": "POST",
            "api_url": "https://api.example.com",
            "api_body": json.dumps(
                {"messages": [{"role": "user", "content": "{{prompt}}"}]}
            ),
        },
        config_id=10,
    )

    with patch(
        "application.services.custom_app_connection_test_service.ModuleLoader.load",
        return_value=(mock_adapter, None),
    ):
        service = CustomAppConnectionTestService(secret_service=secret_service)
        result = await service.test_connection(body)

    assert result.success is False
    assert result.status_code == 401
    assert result.error == "HTTP 401"
    assert result.response_is_json is False
    assert result.response_leaves == []
    secret_service.get_decrypted_secret.assert_called_once_with(10, "api_key")


def test_resolve_api_key_requires_secret():
    secret_service = MagicMock()
    secret_service.is_secret_configured.return_value = False
    service = CustomAppConnectionTestService(secret_service=secret_service)

    with pytest.raises(ValueError, match="authorization secret is required"):
        service._resolve_api_key(TestCustomAppConnectionBody(savedConfigPairs={}))
