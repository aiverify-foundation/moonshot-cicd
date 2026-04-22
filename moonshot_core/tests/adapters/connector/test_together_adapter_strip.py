"""TogetherAdapter forwards stripped kwargs to chat.completions.create."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from adapters.connector.together_adapter import TogetherAdapter
from domain.entities.connector_entity import ConnectorEntity


@pytest.fixture
def connector_entity():
    return ConnectorEntity(
        connector_adapter="together",
        model="meta-llama/Meta-Llama-3-70B-Instruct",
        model_endpoint="https://api.together.xyz/v1",
        params={
            "api_type": "together",
            "base_url": "https://ignored.example",
            "extra_headers": {"X-Test": "1"},
            "temperature": 0.3,
        },
        connector_pre_prompt="",
        connector_post_prompt="",
        system_prompt="",
    )


@pytest.mark.asyncio
async def test_get_response_strips_connector_keys_before_create(
    connector_entity,
):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "ok"

    adapter = TogetherAdapter()
    with (
        patch("adapters.connector.together_adapter.os.getenv", return_value="k"),
        patch("adapters.connector.together_adapter.AsyncTogether") as mock_cls,
        patch.object(adapter, "_process_response", new_callable=AsyncMock, return_value="ok"),
    ):
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        adapter.configure(connector_entity)
        await adapter.get_response("hello")

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert "api_type" not in kwargs
    assert "base_url" not in kwargs
    assert "extra_headers" not in kwargs
    assert kwargs.get("temperature") == 0.3
    assert kwargs.get("model") == connector_entity.model
    assert kwargs.get("messages")


@pytest.mark.asyncio
async def test_get_response_coerces_string_temperature(connector_entity):
    connector_entity.params = {
        "api_type": "together",
        "temperature": "0.25",
        "max_tokens": "64",
    }

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "ok"

    adapter = TogetherAdapter()
    with (
        patch("adapters.connector.together_adapter.os.getenv", return_value="k"),
        patch("adapters.connector.together_adapter.AsyncTogether") as mock_cls,
        patch.object(adapter, "_process_response", new_callable=AsyncMock, return_value="ok"),
    ):
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        adapter.configure(connector_entity)
        await adapter.get_response("hello")

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs.get("temperature") == 0.25
    assert isinstance(kwargs["temperature"], float)
    assert kwargs.get("max_tokens") == 64
    assert isinstance(kwargs["max_tokens"], int)
