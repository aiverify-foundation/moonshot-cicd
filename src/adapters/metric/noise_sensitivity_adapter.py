from pathlib import Path

from ragas import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import NoiseSensitivity

from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.ports.metric_port import MetricPort
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class NoiseSensitivityAdapter(MetricPort):

    ERROR_INIT_MSG = "[NoiseSensitivityAdapter] There was an error initializing the NoiseSensitivityAdapter: {}"
    ERROR_RETRIEVING_CONNECTORS_MSG = (
        "[NoiseSensitivityAdapter] There was an error retrieving metric connectors: {}"
    )
    ERROR_EVALUATING_RESULT_MSG = "[NoiseSensitivityAdapter] There was an error evaluating the individual result: {}"
    ERROR_RETRIEVING_RESULTS_MSG = (
        "[NoiseSensitivityAdapter] There was an error retrieving results: {}"
    )
    NO_CONNECTOR_AVAILABLE_MSG = (
        "[NoiseSensitivityAdapter] No metric connector available for evaluation."
    )
    FAILED_MODEL_PREDICTIONS_MSG = "[NoiseSensitivityAdapter] Failed to get model predictions from the evaluation model."  # noqa: E501
    LOADING_CONNECTOR_MSG = "[NoiseSensitivityAdapter] Loading connector with model '{model}' and adapter '{adapter}'"
    SUCCESSFULLY_LOADED_CONNECTORS_MSG = (
        "[NoiseSensitivityAdapter] Successfully loaded all metric connectors."
    )

    def __init__(self):
        try:
            # Get the filename without the extension
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
        """
        Retrieve the connectors associated with the given metric configuration.

        Args:
            metric_config_entity (MetricConfigEntity): The metric configuration entity.

        Returns:
            dict: A dictionary of connectors associated with the metric configuration.

        Raises:
            Exception: If there is an error retrieving the connectors.
        """

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
        """
        Update the parameters for the metric.

        This method allows updating the parameters used in the metric evaluation.
        If no parameters are provided, the method will simply return without making any changes.

        Args:
            params (dict): A dictionary containing the parameters to update.
        """
        if params:
            self.params = params

    async def get_individual_result(self, entity: MetricIndividualEntity) -> dict:
        """
        Evaluate the result of a single metric entity.

        This method constructs an evaluator prompt using the entity's prompt and predicted result,
        and then evaluates it to determine if an attack was successful.

        Args:
            entity (MetricIndividualEntity): The metric entity to be evaluated.

        Returns:
            dict: A dictionary containing the evaluation details, including the original prompt,
                  predicted value, evaluation prompt, evaluation result, attack success status, and target.

        Raises:
            RuntimeError: If model predictions could not be retrieved.
            Exception: If there is an error during the evaluation process.
        """

        # Check if the selected metric connector is None
        if self.selected_metric_connector is None:
            raise RuntimeError(self.NO_CONNECTOR_AVAILABLE_MSG)

        # Initialize the context precision metric and score the precision of the retrieved contexts
        llm_instance = self.selected_metric_connector.get_client()
        evaluator_llm = LangchainLLMWrapper(llm_instance)
        sample = SingleTurnSample(
            user_input=entity.prompt,
            response=entity.predicted_result.response,
            reference=entity.reference_context,
            retrieved_contexts=entity.predicted_result.context,
        )

        scorer = NoiseSensitivity(llm=evaluator_llm)
        score = await scorer.single_turn_ascore(sample)

        try:
            # Return the evaluation details
            return {
                "prompt": entity.prompt,
                "predicted_value": entity.predicted_result.response,
                "reference_context": entity.reference_context,
                "context": entity.predicted_result.context,
                "target": entity.target,
                "score": score,
            }
        except Exception as e:
            logger.error(self.ERROR_EVALUATING_RESULT_MSG.format(e))
            raise

    async def get_results(self, entities: list[MetricIndividualEntity]) -> dict:
        """
        Retrieve the aggregated results for a list of metric entities.

        This method calculates the noise sensitivity score based on the evaluated results
        of the provided metric entities.

        Args:
            entities (list[MetricIndividualEntity]): The list of metric entities to be evaluated.

        Returns:
            dict: A dictionary containing the noise sensitivity score for the noise sensitivity metric.

        Raises:
            Exception: If there is an error retrieving the results.
        """
        try:
            total_score = sum(
                entity.evaluated_result.get("score", 0) for entity in entities
            )
            average_score = total_score / len(entities)

            return {
                "noise_sensitivity": {
                    "average_score": average_score,
                },
            }
        except Exception as e:
            logger.error(self.ERROR_RETRIEVING_RESULTS_MSG.format(e))
            raise
