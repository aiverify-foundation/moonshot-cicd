import asyncio
import os
from contextlib import contextmanager
from typing import Any, Iterator

import boto3
from botocore.config import Config

from application.services.provider_connector_env_key_service import (
    ProviderConnectorEnvKeyService,
)
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)

BEDROCK_BEARER_TOKEN_ENV = "AWS_BEARER_TOKEN_BEDROCK"

# Flat portal config keys → Bedrock Converse inferenceConfig field names.
_FLAT_INFERENCE_CONFIG_KEYS: dict[str, str] = {
    "temperature": "temperature",
    "maxTokens": "maxTokens",
    "max_tokens": "maxTokens",
    "topP": "topP",
    "top_p": "topP",
}

# Flat portal / env-style keys → boto3.Session kwargs.
_FLAT_SESSION_KEY_ALIASES: dict[str, str] = {
    "region_name": "region_name",
    "aws_access_key_id": "aws_access_key_id",
    "AWS_ACCESS_KEY_ID": "aws_access_key_id",
    "aws_secret_access_key": "aws_secret_access_key",
    "AWS_SECRET_ACCESS_KEY": "aws_secret_access_key",
    "aws_session_token": "aws_session_token",
    "AWS_SESSION_TOKEN": "aws_session_token",
    "profile_name": "profile_name",
}


@contextmanager
def _temporary_bedrock_bearer_token(token: str) -> Iterator[None]:
    """Set AWS_BEARER_TOKEN_BEDROCK for the duration of a Bedrock API-key request."""
    previous = os.environ.get(BEDROCK_BEARER_TOKEN_ENV)
    os.environ[BEDROCK_BEARER_TOKEN_ENV] = token
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(BEDROCK_BEARER_TOKEN_ENV, None)
        else:
            os.environ[BEDROCK_BEARER_TOKEN_ENV] = previous


class AWSBedrockAdapter(ConnectorPort):
    PROVIDER_NAME = "AWS Bedrock"
    SYSTEM_NAME = "aws_bedrock_adapter"
    VERSION = 1
    DEFAULT_MODEL = "openai.gpt-oss-20b-1:0"
    MODEL_TEXTBOX_EXPLANATION = (
        "Enter an AWS Bedrock model ID, e.g. openai.gpt-oss-20b-1:0"
    )
    DEFAULT_CONFIG_PAIRS = {
        "temperature": "1.0",
        "region_name": "us-east-1",
    }

    ERROR_PROCESSING_PROMPT = "[AWSBedrockAdapter] Failed to process prompt."
    ERROR_MISSING_CREDENTIALS = (
        "[AWSBedrockAdapter] Unable to locate AWS credentials. "
        "Paste a Bedrock API key in the Token field (with region_name), "
        "or set aws_access_key_id + Secret Access Key / Token, "
        "or configure AWS credentials in the API process environment."
    )

    """
    Adapter for interacting with the AWS Bedrock service.

    This class provides methods to configure the AWS Bedrock client and retrieve responses
    based on given prompts. It uses the boto3 client to make synchronous requests
    to the AWS Bedrock service and processes the responses to return structured data.

    Attributes:
        connector_entity (ConnectorEntity): The configuration entity for the connector.
        _client (boto3.client): The AWS Bedrock service client.
    """

    def configure(self, connector_entity: ConnectorEntity):
        """
        Configure the AWS Bedrock client with the given connector entity.

        Args:
            connector_entity (ConnectorEntity): The configuration entity for the connector.
        """

        self.connector_entity = connector_entity
        # YAML metric/attack connectors skip DatabaseConnectorConfigService defaults.
        params = {
            **type(self).DEFAULT_CONFIG_PAIRS,
            **dict(self.connector_entity.params or {}),
        }

        # Same order as OpenAI/Together: params override → DB provider key → IAM/env.
        system_name, version = type(self).require_system_name_and_version()
        params_key = str(params.get("api_key") or "").strip()
        if params_key:
            logger.info(
                "[AWSBedrockAdapter] API key resolved from connector params "
                "(e.g. connection test override)"
            )
        else:
            db_key = ProviderConnectorEnvKeyService().get_plain_api_key_for_provider_system_name(
                provider_system_name=system_name,
                version=version,
            )
            if db_key and db_key.strip():
                params["api_key"] = db_key.strip()
                logger.info(
                    "[AWSBedrockAdapter] API key resolved from database "
                    "(llm_provider system_name=%s, version=%s)",
                    system_name,
                    version,
                )

        session_kwargs = self._build_session_kwargs(params)
        self._bedrock_api_key = self._resolve_bedrock_api_key(params, session_kwargs)

        has_access_key = bool(session_kwargs.get("aws_access_key_id"))
        has_secret_key = bool(session_kwargs.get("aws_secret_access_key"))

        if self._bedrock_api_key:
            # Bearer API-key auth: do not require IAM access/secret keys.
            logger.info(
                "[AWSBedrockAdapter] Using Bedrock API key (AWS_BEARER_TOKEN_BEDROCK)"
            )
        else:
            if has_secret_key and not has_access_key:
                raise ValueError(
                    "[AWSBedrockAdapter] aws_access_key_id is required when a "
                    "aws_secret_access_key is provided (set it in advanced parameters). "
                    "Or leave access key empty and put a Bedrock API key in the Token field."
                )
            if has_access_key and not has_secret_key:
                raise ValueError(
                    "[AWSBedrockAdapter] AWS Secret Access Key is required when "
                    "aws_access_key_id is set (use the Token field or aws_secret_access_key)."
                )

        self._session = boto3.Session(**session_kwargs)
        if self._bedrock_api_key is None and self._session.get_credentials() is None:
            raise ValueError(self.ERROR_MISSING_CREDENTIALS)

        # Optional advanced configurations for AWS service client:
        client_kwargs = params.get("client", {})
        if not isinstance(client_kwargs, dict):
            client_kwargs = {}
        else:
            client_kwargs = dict(client_kwargs)
        if "config" in client_kwargs:
            # Convert from JSON configuration dictionary to boto3 Python class:
            client_kwargs["config"] = Config(**client_kwargs["config"])
        # Provide an option to set endpoint_url via moonshot standard, but ignore placeholders
        # like 'DEFAULT' since moonshot currently makes this field mandatory:
        if self.connector_entity.model_endpoint:
            if len(self.connector_entity.model_endpoint) < 8:
                logger.info(
                    "Ignoring placeholder `model_endpoint` (doesn't look like an AWS model_endpoint). Got: %s",
                    self.connector_entity.model_endpoint,
                )
            elif "endpoint_url" in client_kwargs:
                logger.info(
                    "Configured `client.endpoint_url` %s override configured `endpoint` %s",
                    client_kwargs["endpoint_url"],
                    self.connector_entity.model_endpoint,
                )
            else:
                client_kwargs["endpoint_url"] = self.connector_entity.model_endpoint

        if self._bedrock_api_key:
            with _temporary_bedrock_bearer_token(self._bedrock_api_key):
                self._client = self._session.client("bedrock-runtime", **client_kwargs)
        else:
            self._client = self._session.client("bedrock-runtime", **client_kwargs)

    @classmethod
    def _resolve_bedrock_api_key(
        cls, params: dict, session_kwargs: dict
    ) -> str | None:
        """
        Return a Bedrock API key when the portal Token should be used as a bearer token.

        Prefer explicit ``bedrock_api_key`` / ``AWS_BEARER_TOKEN_BEDROCK``. Otherwise, if
        there is no IAM access key id, treat ``api_key`` (UI Token) as the Bedrock API key.
        When ``aws_access_key_id`` is set, ``api_key`` is the IAM secret instead.
        """
        for key in ("bedrock_api_key", BEDROCK_BEARER_TOKEN_ENV):
            value = params.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        if session_kwargs.get("aws_access_key_id"):
            return None

        # Explicit IAM secret in advanced params → not a Bedrock API key path.
        if session_kwargs.get("aws_secret_access_key"):
            return None

        api_key = params.get("api_key")
        if isinstance(api_key, str) and api_key.strip():
            return api_key.strip()
        return None

    @staticmethod
    def _build_session_kwargs(params: dict) -> dict:
        """
        Build boto3.Session kwargs from nested ``session`` and flat portal keys.

        Nested ``session`` values take precedence over flat keys (e.g. ``region_name``).
        When ``aws_access_key_id`` is present, portal Token / ``api_key`` maps to
        ``aws_secret_access_key``. Otherwise ``api_key`` is reserved for Bedrock API key auth.
        """
        session_kwargs: dict = {}
        nested = params.get("session")
        if isinstance(nested, dict):
            session_kwargs.update(nested)

        for flat_key, session_key in _FLAT_SESSION_KEY_ALIASES.items():
            if flat_key not in params:
                continue
            if session_key in session_kwargs:
                continue
            value = params[flat_key]
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    continue
            session_kwargs[session_key] = value

        # IAM mode: Token field is the secret access key.
        if (
            session_kwargs.get("aws_access_key_id")
            and "aws_secret_access_key" not in session_kwargs
        ):
            api_key = params.get("api_key")
            if isinstance(api_key, str) and api_key.strip():
                session_kwargs["aws_secret_access_key"] = api_key.strip()

        return session_kwargs

    @staticmethod
    def _coerce_inference_value(key: str, value: Any) -> Any:
        """Coerce flat string portal params to numeric types for inferenceConfig."""
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if key in {"temperature", "topP"}:
            try:
                return float(stripped)
            except ValueError:
                logger.warning(
                    "Dropping Bedrock inferenceConfig %r: not a valid float (%r)",
                    key,
                    value,
                )
                return None
        if key == "maxTokens":
            try:
                return int(float(stripped))
            except ValueError:
                logger.warning(
                    "Dropping Bedrock inferenceConfig %r: not a valid int (%r)",
                    key,
                    value,
                )
                return None
        return value

    def _build_inference_config(self, params: dict) -> dict | None:
        """
        Merge nested ``inferenceConfig`` with flat portal keys (temperature, etc.).

        Nested ``inferenceConfig`` values take precedence over flat keys.
        """
        inference: dict = {}
        nested = params.get("inferenceConfig")
        if isinstance(nested, dict):
            inference.update(nested)

        for flat_key, inference_key in _FLAT_INFERENCE_CONFIG_KEYS.items():
            if flat_key not in params:
                continue
            if inference_key in inference:
                continue
            coerced = self._coerce_inference_value(inference_key, params[flat_key])
            if coerced is not None:
                inference[inference_key] = coerced

        return inference or None

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        """
        Retrieve a response from the AWS Bedrock service based on the given prompt.

        Args:
            prompt (Any): The prompt to send to the AWS Bedrock service. It can be of any type.

        Returns:
            ConnectorResponseEntity: The response from the AWS Bedrock service.
        """
        connector_prompt = f"{self.connector_entity.connector_pre_prompt}{prompt}{self.connector_entity.connector_post_prompt}"  # noqa: E501

        req_params: dict[str, Any] = {
            "modelId": self.connector_entity.model,
            "messages": [
                {"role": "user", "content": [{"text": connector_prompt}]},
            ],
        }

        if self.connector_entity.system_prompt:
            req_params["system"] = [
                {"text": self.connector_entity.system_prompt},
            ]

        params = self.connector_entity.params or {}
        inference_config = self._build_inference_config(params)
        if inference_config:
            req_params["inferenceConfig"] = inference_config

        if "guardrailConfig" in params:
            req_params["guardrailConfig"] = params["guardrailConfig"]

        try:
            # aioboto3 requires clients to be used as async context managers (so would either need to
            # recreate the client for every request or otherwise hack around to work in Moonshot's API)
            # - so we'll use the official boto3 SDK (synchronous) client and just wrap it with asyncio:
            def _converse():
                if self._bedrock_api_key:
                    with _temporary_bedrock_bearer_token(self._bedrock_api_key):
                        return self._client.converse(**req_params)
                return self._client.converse(**req_params)

            response = await asyncio.to_thread(_converse)
            message = response["output"]["message"]

            if (
                (not message)
                or message["role"] != "assistant"
                or len(message["content"]) < 1
            ):
                raise ValueError(
                    "Bedrock response did not include an assistant message with content. "
                    f"Got: {message}"
                )
            # Ignore any non-text contents, and join together with '\n\n' if multiple are returned:

            return ConnectorResponseEntity(
                response="\n\n".join(
                    map(
                        lambda m: m["text"],
                        filter(lambda m: "text" in m, message["content"]),
                    )
                )
            )
        except Exception as e:
            logger.error(f"{self.ERROR_PROCESSING_PROMPT} {e}")
            raise
