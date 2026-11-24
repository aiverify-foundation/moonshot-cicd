from pathlib import Path

from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.ports.metric_port import MetricPort
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

logger = configure_logger(__name__)


class ExtensionExampleMetricAdapter(MetricPort):
    """
    Example extension metric: exact string match between model output and target.

    Used by the benchmark-extensions overlay; no judge connector required.
    """

    ERROR_INIT_MSG = "[ExtensionExampleMetricAdapter] Error initializing adapter: {}"
    ERROR_RETRIEVING_CONNECTORS_MSG = (
        "[ExtensionExampleMetricAdapter] Error retrieving metric connectors: {}"
    )
    ERROR_EVALUATING_RESULT_MSG = (
        "[ExtensionExampleMetricAdapter] Error evaluating individual result: {}"
    )
    ERROR_RETRIEVING_RESULTS_MSG = (
        "[ExtensionExampleMetricAdapter] Error retrieving results: {}"
    )
    LOADING_CONNECTOR_MSG = (
        "[ExtensionExampleMetricAdapter] Loading connector with model '{model}' "
        "and adapter '{adapter}'"
    )
    SUCCESSFULLY_LOADED_CONNECTORS_MSG = (
        "[ExtensionExampleMetricAdapter] Successfully loaded all metric connectors."
    )

    def __init__(self):
        try:
            metric_id = Path(__file__).stem
            self.metric_config = self.get_metric_config(metric_id)
            if self.metric_config:
                self.metric_connectors = self.get_metric_connectors(self.metric_config)
                if self.metric_connectors:
                    self.selected_metric_connector = next(
                        iter(self.metric_connectors.values()), None
                    )
        except Exception as e:
            logger.error(self.ERROR_INIT_MSG.format(e))
            raise

    def get_metric_connectors(self, metric_config_entity: MetricConfigEntity) -> dict:
        try:
            metric_connectors = {}
            metric_connector_config = metric_config_entity.connector_configurations
            logger.info(
                self.LOADING_CONNECTOR_MSG.format(
                    model=metric_connector_config.model,
                    adapter=metric_connector_config.connector_adapter,
                )
            )
            if metric_connector_config.connector_adapter:
                metric_connector_instance, _ = ModuleLoader.load(
                    metric_connector_config.connector_adapter, ModuleTypes.CONNECTOR
                )
                metric_connector_instance.configure(metric_connector_config)
                metric_connectors["metric"] = metric_connector_instance
                logger.info(self.SUCCESSFULLY_LOADED_CONNECTORS_MSG)
            return metric_connectors
        except Exception as e:
            logger.error(self.ERROR_RETRIEVING_CONNECTORS_MSG.format(e))
            raise

    def update_metric_params(self, params: dict) -> None:
        if params:
            self.params = params

    async def get_individual_result(self, entity: MetricIndividualEntity) -> dict:
        try:
            accuracy = entity.target == entity.predicted_result.response
            return {
                "prompt": entity.prompt,
                "predicted_value": entity.predicted_result.response,
                "target": entity.target,
                "accuracy": accuracy,
                "score": 1.0 if accuracy else 0.0,
            }
        except Exception as e:
            logger.error(self.ERROR_EVALUATING_RESULT_MSG.format(e))
            raise

    async def get_results(self, entities: list[MetricIndividualEntity]) -> dict:
        try:
            accuracy_count = sum(
                1 for entity in entities if entity.evaluated_result.get("accuracy")
            )
            accuracy_rate = (accuracy_count / len(entities)) * 100
            return {
                "accuracy": {
                    "exact_string_match": accuracy_rate,
                },
            }
        except Exception as e:
            logger.error(self.ERROR_RETRIEVING_RESULTS_MSG.format(e))
            raise
