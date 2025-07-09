import json
from typing import Any

import aiohttp
from aiohttp import ClientResponse
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import Session

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class AWSSageMakerAdapter(ConnectorPort):
    """
    Adapter for interacting with AWS SageMaker endpoints.

    This class provides methods to configure and make requests to AWS SageMaker endpoints
    using AWS SigV4 authentication. It processes responses and returns them in a structured format.

    Users will need to export the following environment variables:
        AWS_ACCESS_KEY_ID
        AWS_SECRET_ACCESS_KEY
        AWS_SESSION_TOKEN

    Users will need to set the region and the model name in the moonshot_config.yaml file.

    Attributes:
        connector_entity (ConnectorEntity): The configuration entity for the connector.
        aws_region (str): AWS region where the SageMaker endpoint is deployed.
        aws_model_name (str): Name of the SageMaker model to invoke.
    """

    # Log messages
    LOG_CONFIGURED = (
        "Configured AWS SageMaker adapter with region: {} and model name: {}"
    )
    LOG_PREPARING_REQUEST = "Preparing request to AWS SageMaker endpoint"
    LOG_MAKING_REQUEST = "Making request to SageMaker endpoint: {}"
    LOG_RECEIVED_RESPONSE = "Received response from SageMaker endpoint"
    LOG_PROCESSING_RESPONSE = "Processing response from SageMaker endpoint"

    # Error messages
    ERROR_EMPTY_PROMPT = "No text was provided to process."
    ERROR_MISSING_ENDPOINT = "The AI model endpoint was not specified in the settings."
    ERROR_MISSING_CONNECTOR_ENTITY = "No connector configuration was provided."
    ERROR_MISSING_CREDENTIALS = "Could not find AWS login details."
    ERROR_INVALID_SESSION = "AWS Session could not be initialized."
    ERROR_EMPTY_RESPONSE = "The AI model did not return any response."
    ERROR_MISSING_CHOICES = "The AI model response is missing the expected options."
    ERROR_NO_CHOICES = "The AI model did not provide any response options."
    ERROR_MISSING_MESSAGE = "The AI model response is missing the message part."
    ERROR_MISSING_CONTENT = "The AI model response is missing the content part."
    ERROR_CONFIG_FAILED = "Could not set up connection to the AI model: {}"
    ERROR_GET_RESPONSE = "Problem getting response from the AI model: {}"
    ERROR_UNEXPECTED = "An unexpected error occurred while getting the response: {}"
    ERROR_PROCESSING_RESPONSE = "Problem processing the AI model's response: {}"
    ERROR_UNEXPECTED_PROCESSING = (
        "An unexpected error occurred while processing the response: {}"
    )

    def configure(self, connector_entity: ConnectorEntity):
        """
        Configure the AWS SageMaker client with the given connector entity.

        Args:
            connector_entity (ConnectorEntity): The configuration entity for the connector.
        """
        try:
            if connector_entity is None:
                logger.error(self.ERROR_MISSING_CONNECTOR_ENTITY)
                raise ValueError(self.ERROR_MISSING_CONNECTOR_ENTITY)

            self.connector_entity = connector_entity

            # Initialise AWS session
            params = self.connector_entity.params or {}
            self.aws_region = params.get("session", {}).get(
                "region_name", "ap-southeast-1"
            )
            self.aws_model = self.connector_entity.model
            if not self.aws_model:
                raise ValueError(self.ERROR_MISSING_ENDPOINT)

            logger.info(self.LOG_CONFIGURED.format(self.aws_region, self.aws_model))
        except Exception as e:
            logger.error(self.ERROR_CONFIG_FAILED.format(str(e)))
            raise

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        """
        Retrieve a response from the AWS SageMaker service based on the given prompt.

        Args:
            prompt (Any): The prompt to send to the AWS SageMaker service.

        Returns:
            ConnectorResponseEntity: The response from the AWS SageMaker service.

        Raises:
            ValueError: If the prompt is invalid or configuration is missing
            aiohttp.ClientError: If there is a network or HTTP error
        """
        try:
            logger.info(self.LOG_PREPARING_REQUEST)
            if not prompt:
                raise ValueError(self.ERROR_EMPTY_PROMPT)

            connector_prompt = f"{self.connector_entity.connector_pre_prompt}{prompt}{self.connector_entity.connector_post_prompt}"  # noqa: E501
            if self.connector_entity.system_prompt:
                payload = {
                    "messages": [
                        {
                            "role": "system",
                            "content": self.connector_entity.system_prompt,
                        },
                        {"role": "user", "content": connector_prompt},
                    ],
                }
            else:
                payload = {
                    "messages": [
                        {"role": "user", "content": connector_prompt},
                    ],
                }

            # Add params to the payload
            if self.connector_entity.params:
                payload.update(self.connector_entity.params)

            # aws signed header
            aws_sagemaker_endpoint_url = f"https://runtime.sagemaker.{self.aws_region}.amazonaws.com/endpoints/{self.aws_model}/invocations"  # noqa: E501
            request = AWSRequest(
                method="POST",
                url=aws_sagemaker_endpoint_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
            )
            session = Session()
            if not session:
                raise ValueError(self.ERROR_INVALID_SESSION)
            credentials = session.get_credentials()
            if not credentials:
                raise ValueError(self.ERROR_MISSING_CREDENTIALS)

            SigV4Auth(credentials, "sagemaker", self.aws_region).add_auth(request)
            signed_header = dict(request.headers)

            logger.info(self.LOG_MAKING_REQUEST.format(aws_sagemaker_endpoint_url))
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    str(request.url),
                    headers=signed_header,
                    json=payload,
                ) as response:
                    logger.info(self.LOG_RECEIVED_RESPONSE)
                    return ConnectorResponseEntity(
                        response=await self._process_response(response)
                    )
        except (ValueError, aiohttp.ClientError) as e:
            logger.error(self.ERROR_GET_RESPONSE.format(str(e)))
            raise
        except Exception as e:
            logger.error(self.ERROR_UNEXPECTED.format(str(e)))
            raise

    async def _process_response(self, response: ClientResponse) -> str:
        """
        Process the SageMaker endpoint response and extract the model's output.

        Args:
            response (ClientResponse): The HTTP response from SageMaker endpoint.

        Returns:
            str: The extracted response content from the model.

        Raises:
            KeyError: If required fields are missing in the response structure
            ValueError: If response format is invalid or empty
            Exception: For any other unexpected errors during processing
        """
        try:
            logger.info(self.LOG_PROCESSING_RESPONSE)
            json_response = await response.json()

            if not json_response:
                raise ValueError(self.ERROR_EMPTY_RESPONSE)

            if "choices" not in json_response:
                raise ValueError(self.ERROR_MISSING_CHOICES)

            if not json_response["choices"]:
                raise ValueError(self.ERROR_NO_CHOICES)

            if (
                "message" not in json_response["choices"][0]
                or json_response["choices"][0]["message"] is None
            ):
                raise ValueError(self.ERROR_MISSING_MESSAGE)

            if (
                "content" not in json_response["choices"][0]["message"]
                or json_response["choices"][0]["message"]["content"] is None
            ):
                raise ValueError(self.ERROR_MISSING_CONTENT)

            return json_response["choices"][0]["message"]["content"]

        except ValueError as exception:
            logger.error(
                f"{self.ERROR_PROCESSING_RESPONSE.format(str(exception))} Raw response: {await response.text()}"
            )
            raise
        except Exception as exception:
            logger.error(self.ERROR_UNEXPECTED_PROCESSING.format(str(exception)))
            raise
