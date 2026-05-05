import logging
from abc import ABC, abstractmethod

from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.services.app_config import AppConfig

# Initialize a logger for this module
logger = logging.getLogger(__name__)


class MetricPort(ABC):
    """
    MetricPort is an abstract base class that defines the interface for metric-related operations.
    """

    METRIC_CONFIG_NOT_FOUND_MSG = "[MetricPort] Metric config not found for {}"
    ERROR_RETRIEVING_CONFIG_MSG = (
        "[MetricPort] Error retrieving metric config for {}: {}"
    )

    def get_metric_config(self, metric_id: str) -> MetricConfigEntity:
        """
        Retrieve the configuration for a specific metric.

        Args:
            metric_id (str): The ID of the metric.

        Returns:
            MetricConfigEntity: The configuration entity for the metric.

        Raises:
            ValueError: If the metric configuration is not found.
        """
        try:
            app_config = AppConfig()
            metric_config = app_config.get_metric_config(metric_id)
            if metric_config is None:
                logger.error(self.METRIC_CONFIG_NOT_FOUND_MSG.format(metric_id))
                raise ValueError(self.METRIC_CONFIG_NOT_FOUND_MSG.format(metric_id))
            return metric_config
        except Exception as e:
            logger.error(self.ERROR_RETRIEVING_CONFIG_MSG.format(metric_id, e))
            raise

    @abstractmethod
    def get_metric_connectors(self, metric_config_entity: MetricConfigEntity) -> dict:
        """
        Retrieve the connectors associated with the given metric configuration.

        Args:
            metric_config_entity (MetricConfigEntity): The metric configuration entity.

        Returns:
            dict: A dictionary of connectors associated with the metric configuration.
        """
        pass

    @abstractmethod
    def update_metric_params(self, params: dict) -> None:
        """
        Update the metric parameters with the provided values.

        This method allows the user to modify the existing metric parameters
        by providing a dictionary of new parameter values. The implementation
        should ensure that the parameters are validated and updated correctly.

        Args:
            params (dict): A dictionary containing the metric parameters to be updated.
                        The keys should correspond to the parameter names, and the
                        values should be the new values to set.

        Raises:
            ValueError: If any of the provided parameters are invalid or cannot be updated.
        """
        pass

    @abstractmethod
    async def get_individual_result(self, entity: MetricIndividualEntity) -> dict:
        """
        Evaluate the result of a single metric entity.

        Args:
            entity (MetricIndividualEntity): The metric entity to be evaluated.

        Returns:
            dict: Per-result payload persisted as ``str(dict)`` on
                  ``benchmark_run_test_prompt.evaluation_prediction_result``.
                  Prefer a consistent subset so UIs can parse blobs without
                  relying on connector-specific quirks.

            Typical keys (implementations SHOULD include):

            Required for binary-style metrics:

            - ``prompt`` (str): Task prompt text.
            - ``predicted_value`` (str): Model output being graded.
            - ``target`` (str): Expected / reference label or policy target.
            - ``score`` (float): In ``[0.0, 1.0]`` (or continuous sub-range if documented).

            Optional (use when relevant):

            - ``accuracy`` (bool): Shortcut for strict match / pass-fail semantics;
              same convention as ``AccuracyAdapter.get_individual_result`` when present.
            - ``evaluated_prompt`` (str): Prompt sent to an evaluator LLM or rubric step.
            - ``evaluated_response`` (str): Short categorical evaluator label,
              e.g. ``safe`` | ``unsafe`` | ``refuse`` | ``non-refusal``.
            - Connector- or metric-specific extras: ``evaluated_raw_response``,
              ``attack_success``, ``context``, etc.

            Downstream callers may derive UI colour from ``score`` or ``accuracy``
            (when persisted in the blob) and short labels from ``evaluated_response``.
        """
        pass

    @abstractmethod
    async def get_results(self, entities: list[MetricIndividualEntity]) -> dict:
        """
        Retrieve the aggregated results for a list of metric entities.

        Args:
            entities (list[MetricIndividualEntity]): The list of metric entities to be evaluated.

        Returns:
            dict: A dictionary containing the aggregated results for the metrics.
        """
        pass
