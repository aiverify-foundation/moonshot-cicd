import asyncio
from typing import Any

import boto3
from botocore.config import Config

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class AWSBedrockAdapter(ConnectorPort):

    ERROR_PROCESSING_PROMPT = "[AWSBedrockAdapter] Failed to process prompt."

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

        # Initialise AWS session:
        session_kwargs = self.connector_entity.params.get("session", {})

        self._session = boto3.Session(**session_kwargs)

        # Optional advanced configurations for AWS service client:
        client_kwargs = self.connector_entity.params.get("client", {})
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
        self._client = self._session.client("bedrock-runtime", **client_kwargs)

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        """
        Retrieve a response from the AWS Bedrock service based on the given prompt.

        Args:
            prompt (Any): The prompt to send to the AWS Bedrock service. It can be of any type.

        Returns:
            ConnectorResponseEntity: The response from the AWS Bedrock service.
        """
        connector_prompt = f"{self.connector_entity.connector_pre_prompt}{prompt}{self.connector_entity.connector_post_prompt}"  # noqa: E501

        req_params = {
            "modelId": self.connector_entity.model,
            "messages": [
                {"role": "user", "content": [{"text": connector_prompt}]},
            ],
        }

        for key in ["inferenceConfig", "guardrailConfig"]:
            if key in self.connector_entity.params:
                req_params[key] = self.connector_entity.params[key]

        try:
            # aioboto3 requires clients to be used as async context managers (so would either need to
            # recreate the client for every request or otherwise hack around to work in Moonshot's API)
            # - so we'll use the official boto3 SDK (synchronous) client and just wrap it with asyncio:
            response = await asyncio.to_thread(
                lambda: self._client.converse(**req_params)
            )
            message = response["output"]["message"]

            if (
                (not message)
                or message["role"] != "assistant"
                or len(message["content"]) < 1
            ):
                raise ValueError(
                    "Bedrock response did not include an assistant message with content. Got: %s",
                    message,
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
            raise (e)
