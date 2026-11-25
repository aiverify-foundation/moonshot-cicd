"""
E2E stub connector for the benchmark-extensions overlay.

Always answers "OK" without any network call, so extension-provider tests
need no API key and no external service. Copied into a temporary overlay by
system_test/utils/extensionOverlay.js.
"""

from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort


class OkConnectorAdapter(ConnectorPort):
    PROVIDER_NAME = "E2E OK Connector"
    SYSTEM_NAME = "e2e_ok_connector"
    VERSION = 1
    DEFAULT_MODEL = "ok-model"
    MODEL_TEXTBOX_EXPLANATION = "Any model name; the stub ignores it"
    DEFAULT_CONFIG_PAIRS = {}

    def configure(self, connector_entity):
        self.connector_entity = connector_entity

    async def get_response(self, prompt):
        return ConnectorResponseEntity(response="OK")
