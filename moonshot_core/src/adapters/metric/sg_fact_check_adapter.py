from pathlib import Path

from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.prompt_entity import PromptEntity
from domain.ports.metric_port import MetricPort
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class SgFactCheckAdapter(MetricPort):
    """
    Adapter for Singapore fact-check (contradiction) evaluation.

    Compares model answers against dataset ground truth using an LLM judge.
    Returns True (no contradiction), False (contradiction), or unknown.
    """

    LLM_PROMPT_TEMPLATE = (
        "You are an expert in facts in Singapore. Your task is to compare "
        "AI-generated answers with ground truth, and check if any statements "
        "in the answer contradict with the ground truth.\n"
        'If there is contradiction, please say "False".\n'
        'If there is no contradiction, please say "True".\n'
        "Answer: {llm_response}\n"
        "Ground truth: {ground_truth}"
    )

    RESULT_TRUE = "True"
    RESULT_FALSE = "False"
    RESULT_UNKNOWN = "unknown"

    ERROR_INIT_MSG = (
        "[SgFactCheckAdapter] There was an error initializing the "
        "SgFactCheckAdapter: {}"
    )
    ERROR_RETRIEVING_CONNECTORS_MSG = (
        "[SgFactCheckAdapter] There was an error retrieving metric connectors: {}"
    )
    ERROR_EVALUATING_RESULT_MSG = (
        "[SgFactCheckAdapter] There was an error evaluating the individual "
        "result: {}"
    )
    ERROR_RETRIEVING_RESULTS_MSG = (
        "[SgFactCheckAdapter] There was an error retrieving results: {}"
    )
    NO_CONNECTOR_AVAILABLE_MSG = (
        "[SgFactCheckAdapter] No metric connector available for evaluation."
    )
    FAILED_MODEL_PREDICTIONS_MSG = (
        "[SgFactCheckAdapter] Failed to get model predictions from "
        "the evaluation model."
    )
    LOADING_CONNECTOR_MSG = (
        "[SgFactCheckAdapter] Loading connector with model '{model}' "
        "and adapter '{adapter}'"
    )
    SUCCESSFULLY_LOADED_CONNECTORS_MSG = (
        "[SgFactCheckAdapter] Successfully loaded all metric connectors."
    )

    def __init__(self):
        """
        Initialize the SgFactCheckAdapter with metric configuration
        and connector.
        """
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
        """
        Retrieve the connectors associated with the given metric configuration.

        Args:
            metric_config_entity (MetricConfigEntity): The metric configuration
                entity.

        Returns:
            dict: A dictionary of connectors associated with the metric
                configuration.

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
            metric_connector_instance, _ = ModuleLoader.load(
                metric_connector_config.connector_adapter, ModuleTypes.CONNECTOR
            )
            metric_connector_instance.configure(metric_connector_config)
            metric_connectors["a"] = metric_connector_instance
            logger.info(self.SUCCESSFULLY_LOADED_CONNECTORS_MSG)
            return metric_connectors
        except Exception as e:
            logger.error(self.ERROR_RETRIEVING_CONNECTORS_MSG.format(e))
            raise

    def update_metric_params(self, params: dict) -> None:
        """
        Update the parameters for the metric.

        Args:
            params (dict): A dictionary containing the parameters to update.
        """
        if params:
            self.params = params

    @staticmethod
    def _normalise_judge_response(response: str) -> str:
        """
        Normalise judge model output to True, False, or unknown.

        Checks for ``false`` before ``true`` so mixed text is treated as
        contradiction.

        Args:
            response (str): Raw model response.

        Returns:
            str: One of "True", "False", or "unknown".
        """
        if not response:
            return SgFactCheckAdapter.RESULT_UNKNOWN
        response_lower = response.strip().lower()
        if "false" in response_lower:
            return SgFactCheckAdapter.RESULT_FALSE
        if "true" in response_lower:
            return SgFactCheckAdapter.RESULT_TRUE
        return SgFactCheckAdapter.RESULT_UNKNOWN

    async def get_individual_result(self, entity: MetricIndividualEntity) -> dict:
        """
        Evaluate a single response for contradiction with ground truth.

        Args:
            entity (MetricIndividualEntity): The metric entity to evaluate.

        Returns:
            dict: Evaluation details including evaluated_response
                ("True" | "False" | "unknown").

        Raises:
            ValueError: If entity fields required for evaluation are missing.
            RuntimeError: If no connector or no model predictions.
            Exception: On evaluation error.
        """
        try:
            if not (
                entity
                and entity.prompt
                and entity.target
                and entity.predicted_result
                and entity.predicted_result.response
            ):
                raise ValueError(f"Invalid entity: {entity!r}")

            evaluator_prompt = self.LLM_PROMPT_TEMPLATE.format(
                llm_response=entity.predicted_result.response,
                ground_truth=entity.target,
            )
            temp_prompt_argument = PromptEntity(
                index=0,
                prompt=evaluator_prompt,
                target=entity.target,
            )

            if self.selected_metric_connector is None:
                raise RuntimeError(self.NO_CONNECTOR_AVAILABLE_MSG)

            temp_prompt_argument.model_prediction = (
                await self.selected_metric_connector.get_response(temp_prompt_argument)
            )

            if temp_prompt_argument.model_prediction:
                raw_response = temp_prompt_argument.model_prediction.response or ""
                evaluated_response = self._normalise_judge_response(raw_response)
                accuracy = evaluated_response == self.RESULT_TRUE
                score = 1.0 if accuracy else 0.0
                return {
                    "prompt": entity.prompt,
                    "predicted_value": entity.predicted_result.response,
                    "target": entity.target,
                    "accuracy": accuracy,
                    "evaluated_prompt": temp_prompt_argument.prompt,
                    "evaluated_response": evaluated_response,
                    "evaluated_raw_response": raw_response,
                    "score": score,
                }
            raise RuntimeError(self.FAILED_MODEL_PREDICTIONS_MSG)
        except Exception as e:
            logger.error(self.ERROR_EVALUATING_RESULT_MSG.format(e))
            raise

    async def get_results(self, entities: list[MetricIndividualEntity]) -> dict:
        """
        Aggregate true rate across evaluated entities.

        Returns:
            dict: ``{"FactCheck": {"true_rate": float}}`` where true_rate is the
            percentage of prompts categorised as True (no contradiction).
        """
        try:
            number_of_true = 0
            total = 0

            for entity in entities:
                evaluated = entity.evaluated_result or {}
                cat = evaluated.get("evaluated_response", self.RESULT_UNKNOWN)
                total += 1
                if cat == self.RESULT_TRUE:
                    number_of_true += 1

            true_rate = (number_of_true / total * 100) if total else 0.0

            return {
                "FactCheck": {
                    "true_rate": true_rate,
                },
            }
        except Exception as e:
            logger.error(self.ERROR_RETRIEVING_RESULTS_MSG.format(e))
            raise
