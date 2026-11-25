"""
E2E stub connector that always fails.

Used for negative connection-test and run-failure checks. Copied into a
temporary overlay by system_test/utils/extensionOverlay.js.
"""

from domain.ports.connector_port import ConnectorPort


class ErrorConnectorAdapter(ConnectorPort):
    PROVIDER_NAME = "E2E Error Connector"
    SYSTEM_NAME = "e2e_error_connector"
    VERSION = 1
    DEFAULT_MODEL = "error-model"
    MODEL_TEXTBOX_EXPLANATION = "Any model name; the stub always fails"
    DEFAULT_CONFIG_PAIRS = {}

    def configure(self, connector_entity):
        self.connector_entity = connector_entity

    async def get_response(self, prompt):
        raise RuntimeError("stub failure")
