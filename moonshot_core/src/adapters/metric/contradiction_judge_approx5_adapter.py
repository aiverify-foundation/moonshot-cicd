import json
import re
from pathlib import Path

from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.ports.metric_port import MetricPort
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

MAX_GROUND_TRUTH_FACTS = 20


def _read_prompt(filename: str) -> str:
    """Load a verbatim prompt file from metric/prompt_templates."""
    path = Path(__file__).resolve().parent / "prompt_templates" / filename
    prompt = path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"Prompt file is empty: {path}")
    return prompt


class ContradictionJudgeApprox5Adapter(MetricPort):
    """
    Contradiction judge with ±5% numeric tolerance.

    Extracts atomic claims from the ground-truth answer, then asks one LLM
    whether the model response contradicts those claims. Dates and years must
    match exactly. Omission alone is not a contradiction.

    ``contradict`` 0 (no contradiction) maps to ``True`` / score 1.0.
    ``contradict`` 1 maps to ``False`` / score 0.0.
    """

    FACT_EXTRACTION_PROMPT_TEMPLATE = _read_prompt(
        "contradiction_judge_approx5_fact_extraction_prompt.txt"
    )
    JUDGE_SYSTEM_PROMPT = _read_prompt("contradiction_judge_approx5_prompt.txt")

    ERROR_INIT_MSG = (
        "[ContradictionJudgeApprox5Adapter] There was an error initializing "
        "the ContradictionJudgeApprox5Adapter: %s"
    )
    ERROR_RETRIEVING_CONNECTORS_MSG = (
        "[ContradictionJudgeApprox5Adapter] There was an error retrieving "
        "metric connectors: %s"
    )
    ERROR_EVALUATING_RESULT_MSG = (
        "[ContradictionJudgeApprox5Adapter] There was an error evaluating "
        "the individual result: %s"
    )
    ERROR_RETRIEVING_RESULTS_MSG = (
        "[ContradictionJudgeApprox5Adapter] There was an error retrieving "
        "results: %s"
    )
    NO_CONNECTOR_AVAILABLE_MSG = (
        "[ContradictionJudgeApprox5Adapter] No metric connector available "
        "for evaluation."
    )
    FAILED_MODEL_PREDICTIONS_MSG = (
        "[ContradictionJudgeApprox5Adapter] Failed to get model predictions "
        "from the evaluation model."
    )
    LOADING_CONNECTOR_MSG = (
        "[ContradictionJudgeApprox5Adapter] Loading connector with model "
        "'{model}' and adapter '{adapter}'"
    )
    SUCCESSFULLY_LOADED_CONNECTORS_MSG = (
        "[ContradictionJudgeApprox5Adapter] Successfully loaded all metric "
        "connectors."
    )

    def __init__(self):
        """
        Initialize the adapter from metric configuration and judge connectors.
        """
        try:
            metric_id = Path(__file__).stem
            self.metric_config = self.get_metric_config(metric_id)
            self.fact_connector = None
            self.judge_connector = None
            if self.metric_config:
                self.metric_connectors = self.get_metric_connectors(self.metric_config)
                self.fact_connector = self.metric_connectors.get("fact")
                self.judge_connector = self.metric_connectors.get("judge")
        except Exception as e:
            logger.error(self.ERROR_INIT_MSG, e)
            raise

    def get_metric_connectors(self, metric_config_entity: MetricConfigEntity) -> dict:
        """
        Load two connectors from the same YAML configuration.

        The fact-extraction connector has an empty system prompt. The judge
        connector uses the approx5 system prompt. Separate instances keep
        concurrent evaluations from sharing a mutable system prompt.

        Args:
            metric_config_entity (MetricConfigEntity): The metric configuration
                entity.

        Returns:
            dict: ``{"fact": connector, "judge": connector}``.
        """
        try:
            metric_connector_config = metric_config_entity.connector_configurations
            logger.info(
                self.LOADING_CONNECTOR_MSG.format(
                    model=metric_connector_config.model,
                    adapter=metric_connector_config.connector_adapter,
                )
            )
            fact_config = metric_connector_config.model_copy(
                update={"system_prompt": ""}
            )
            judge_config = metric_connector_config.model_copy(
                update={"system_prompt": self.JUDGE_SYSTEM_PROMPT}
            )
            fact_connector = self._load_connector(fact_config)
            judge_connector = self._load_connector(judge_config)
            logger.info(self.SUCCESSFULLY_LOADED_CONNECTORS_MSG)
            return {"fact": fact_connector, "judge": judge_connector}
        except Exception as e:
            logger.error(self.ERROR_RETRIEVING_CONNECTORS_MSG, e)
            raise

    @staticmethod
    def _load_connector(connector_config):
        """Load and configure one connector instance."""
        connector, _ = ModuleLoader.load(
            connector_config.connector_adapter, ModuleTypes.CONNECTOR
        )
        connector.configure(connector_config)
        return connector

    def update_metric_params(self, params: dict) -> None:
        """
        Update the parameters for the metric.

        Args:
            params (dict): A dictionary containing the parameters to update.
        """
        if params:
            self.params = params

    @staticmethod
    def _extract_json_object(text: str):
        """Parse a JSON object, stripping an optional markdown fence."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        return json.loads(cleaned)

    @staticmethod
    def _salvage_facts_from_json(text: str) -> list[str]:
        """Best-effort recovery of fact strings from truncated JSON."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        match = re.search(r'"facts"\s*:\s*\[(.*)', cleaned, re.DOTALL)
        if not match:
            return []
        body = match.group(1)
        facts = re.findall(r'"((?:[^"\\]|\\.)*)"', body)
        return [fact.strip() for fact in facts if fact.strip()]

    @classmethod
    def _parse_fact_extraction_response(
        cls,
        raw: str,
        max_facts: int = MAX_GROUND_TRUTH_FACTS,
    ) -> list[str]:
        """Parse fact-extraction JSON into at most ``max_facts`` claims."""
        facts: list[str] = []
        try:
            parsed = cls._extract_json_object(raw)
            extracted = parsed.get("facts") if isinstance(parsed, dict) else None
            if isinstance(extracted, list):
                facts = [str(item).strip() for item in extracted if str(item).strip()]
        except json.JSONDecodeError:
            facts = cls._salvage_facts_from_json(raw)
        if not facts:
            raise ValueError(f"Failed to parse fact extraction JSON: {raw!r}")
        return facts[:max_facts]

    @staticmethod
    def _build_contradiction_user_message(
        question_text: str,
        ground_truth_facts: list[str],
        response_text: str,
    ) -> str:
        """Build the judge user message from question, claims, and response."""
        claims = "\n".join(f"- {fact}" for fact in ground_truth_facts) or "(none)"
        return (
            f"Question:\n{question_text}\n\n"
            f"Ground truth claims:\n{claims}\n\n"
            f"Assistant response:\n{response_text}"
        )

    @classmethod
    def _parse_contradiction_response(cls, raw: str) -> tuple[int, str]:
        """Parse ``{contradict, reason}`` from the judge reply."""
        try:
            parsed = cls._extract_json_object(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Expected JSON object from contradiction judge: {raw!r}"
            ) from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected JSON object from contradiction judge: {raw!r}")
        contradict = parsed.get("contradict")
        if contradict not in (0, 1):
            raise ValueError(f"Invalid contradict value: {contradict!r}")
        reason = str(parsed.get("reason", "")).strip()
        return int(contradict), reason

    async def _extract_ground_truth_facts(self, answer: str) -> list[str]:
        """Extract claims from ground truth. Retry once when the reply is empty."""
        prompt = self.FACT_EXTRACTION_PROMPT_TEMPLATE.replace("{text}", answer)
        last_error: Exception | None = None
        for attempt in range(2):
            prediction = await self.fact_connector.get_response(prompt)
            raw = ""
            if prediction is not None:
                raw = prediction.response or ""
            try:
                return self._parse_fact_extraction_response(raw)
            except ValueError as exc:
                last_error = exc
                if attempt == 0 and not raw.strip():
                    continue
                raise
        assert last_error is not None
        raise last_error

    async def get_individual_result(self, entity: MetricIndividualEntity) -> dict:
        """
        Evaluate one response for contradiction with ground-truth claims.

        Args:
            entity (MetricIndividualEntity): The metric entity to evaluate.

        Returns:
            dict: Evaluation details. ``evaluated_response`` is ``True`` when
            the judge reports no contradiction and ``False`` when it does.

        Raises:
            ValueError: If required entity fields are missing, or a judge
                reply cannot be parsed.
            RuntimeError: If a required connector is missing or returns no
                prediction.
        """
        try:
            if not (
                entity
                and entity.prompt
                and entity.predicted_result
                and entity.predicted_result.response
            ):
                raise ValueError(f"Invalid entity: {entity!r}")

            judge_connector = getattr(self, "judge_connector", None)
            fact_connector = getattr(self, "fact_connector", None)
            if judge_connector is None:
                raise RuntimeError(self.NO_CONNECTOR_AVAILABLE_MSG)

            answer = "" if entity.target is None else str(entity.target)
            if answer.strip():
                if fact_connector is None:
                    raise RuntimeError(self.NO_CONNECTOR_AVAILABLE_MSG)
                ground_truth_facts = await self._extract_ground_truth_facts(answer)
            else:
                ground_truth_facts = []

            user_message = self._build_contradiction_user_message(
                str(entity.prompt),
                ground_truth_facts,
                entity.predicted_result.response,
            )
            judge_prediction = await judge_connector.get_response(user_message)
            if not judge_prediction:
                raise RuntimeError(self.FAILED_MODEL_PREDICTIONS_MSG)

            raw_response = judge_prediction.response or ""
            contradict, reason = self._parse_contradiction_response(raw_response)
            evaluated_response = (
                self.RESULT_PASS if contradict == 0 else self.RESULT_FAIL
            )
            score = self.score_from_evaluated_response(evaluated_response)
            return {
                "prompt": entity.prompt,
                "predicted_value": entity.predicted_result.response,
                "target": entity.target,
                "accuracy": score == 1.0,
                "evaluated_prompt": user_message,
                "evaluated_response": evaluated_response,
                "evaluated_raw_response": raw_response,
                "score": score,
                "ground_truth_facts": ground_truth_facts,
                "contradict": contradict,
                "reason": reason,
            }
        except Exception as e:
            logger.error(self.ERROR_EVALUATING_RESULT_MSG, e)
            raise

    async def get_results(self, entities: list[MetricIndividualEntity]) -> dict:
        """
        Aggregate the no-contradiction rate across evaluated entities.

        Returns:
            dict: ``{"ContradictionJudgeApprox5": {"no_contradiction_rate": float}}``
            where the rate is the percentage of prompts categorised as True.
        """
        try:
            number_of_true = 0
            total = 0

            for entity in entities:
                evaluated = entity.evaluated_result or {}
                category = evaluated.get("evaluated_response", self.RESULT_UNKNOWN)
                total += 1
                if category == self.RESULT_PASS:
                    number_of_true += 1

            no_contradiction_rate = (number_of_true / total * 100) if total else 0.0
            return {
                "ContradictionJudgeApprox5": {
                    "no_contradiction_rate": no_contradiction_rate,
                },
            }
        except Exception as e:
            logger.error(self.ERROR_RETRIEVING_RESULTS_MSG, e)
            raise
