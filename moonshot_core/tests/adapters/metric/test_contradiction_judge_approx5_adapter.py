import json
from pathlib import Path

import pytest

from adapters.metric.contradiction_judge_approx5_adapter import (
    ContradictionJudgeApprox5Adapter,
)
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity


class MockConnector:
    """Records prompts and returns queued or fixed judge text."""

    def __init__(self, response_value: str = ""):
        self.configured_with = None
        self.calls: list[str] = []
        self.response_value = response_value
        self.responses: list[str | None] | None = None

    def configure(self, config):
        self.configured_with = config

    async def get_response(self, prompt):
        self.calls.append(prompt)
        if self.responses is not None:
            value = self.responses.pop(0)
        else:
            value = self.response_value
        if value is None:
            return None
        return ConnectorResponseEntity(response=value)


def _entity(
    prompt: str = "What is Singapore's population?",
    response: str = "About 6 million.",
    target: str = "Singapore's population is 5.92 million.",
) -> MetricIndividualEntity:
    return MetricIndividualEntity(
        prompt=prompt,
        predicted_result=ConnectorResponseEntity(response=response),
        target=target,
        evaluated_result={},
    )


def _adapter(
    fact: MockConnector, judge: MockConnector
) -> ContradictionJudgeApprox5Adapter:
    adapter = ContradictionJudgeApprox5Adapter.__new__(ContradictionJudgeApprox5Adapter)
    adapter.fact_connector = fact
    adapter.judge_connector = judge
    return adapter


class TestContradictionJudgeApprox5Adapter:
    """Test suite for ContradictionJudgeApprox5Adapter."""

    @pytest.fixture
    def mock_metric_config(self):
        """Metric config whose connector is cloned for fact and judge calls."""
        return MetricConfigEntity(
            name="contradiction_judge_approx5_adapter",
            connector_configurations=ConnectorEntity(
                connector_adapter="aws_bedrock_adapter",
                model="openai.gpt-oss-20b-1:0",
                system_prompt="should-be-replaced",
                params={"region_name": "us-east-1"},
            ),
        )

    def test_init_success(self, monkeypatch, mock_metric_config):
        """Initialization loads separate fact and judge connectors."""
        created: list[MockConnector] = []

        def mock_get_metric_config(self, metric_id):
            return mock_metric_config

        def mock_module_loader_load(adapter, module_type):
            connector = MockConnector()
            created.append(connector)
            return connector, None

        monkeypatch.setattr(Path, "stem", "contradiction_judge_approx5_adapter")
        monkeypatch.setattr(
            ContradictionJudgeApprox5Adapter,
            "get_metric_config",
            mock_get_metric_config,
        )
        monkeypatch.setattr(
            "adapters.metric.contradiction_judge_approx5_adapter.ModuleLoader.load",
            mock_module_loader_load,
        )

        adapter = ContradictionJudgeApprox5Adapter()

        assert adapter.fact_connector is created[0]
        assert adapter.judge_connector is created[1]
        assert created[0].configured_with.system_prompt == ""
        assert (
            created[1].configured_with.system_prompt
            == ContradictionJudgeApprox5Adapter.JUDGE_SYSTEM_PROMPT
        )
        assert "±5%" in created[1].configured_with.system_prompt

    def test_get_metric_connectors_judge_system_prompt_only(
        self, monkeypatch, mock_metric_config
    ):
        """Only the judge connector receives the approx5 system prompt."""
        created: list[MockConnector] = []

        def mock_module_loader_load(adapter, module_type):
            connector = MockConnector()
            created.append(connector)
            return connector, None

        monkeypatch.setattr(
            "adapters.metric.contradiction_judge_approx5_adapter.ModuleLoader.load",
            mock_module_loader_load,
        )

        adapter = ContradictionJudgeApprox5Adapter.__new__(
            ContradictionJudgeApprox5Adapter
        )
        result = adapter.get_metric_connectors(mock_metric_config)

        assert result["fact"] is created[0]
        assert result["judge"] is created[1]
        assert created[0].configured_with.system_prompt == ""
        assert (
            created[1].configured_with.system_prompt
            == ContradictionJudgeApprox5Adapter.JUDGE_SYSTEM_PROMPT
        )
        assert "strict ±5% margin" in created[1].configured_with.system_prompt
        assert created[0].configured_with.model == "openai.gpt-oss-20b-1:0"

    def test_parse_fenced_and_truncated_facts(self):
        """Fenced JSON and a truncated facts array both yield claims."""
        fenced = '```json\n{"facts": ["alpha", "beta"]}\n```'
        truncated = '{"facts": ["alpha", "beta"'

        assert ContradictionJudgeApprox5Adapter._parse_fact_extraction_response(
            fenced
        ) == ["alpha", "beta"]
        assert ContradictionJudgeApprox5Adapter._parse_fact_extraction_response(
            truncated
        ) == ["alpha", "beta"]

    def test_parse_fact_extraction_caps_at_twenty(self):
        """Fact extraction keeps at most 20 claims."""
        facts = [f"claim {index}" for index in range(25)]
        raw = json.dumps({"facts": facts})

        parsed = ContradictionJudgeApprox5Adapter._parse_fact_extraction_response(raw)

        assert parsed == facts[:20]

    def test_parse_bad_judge_json_raises(self):
        """Unparseable judge output raises instead of scoring."""
        with pytest.raises(ValueError, match="contradiction judge"):
            ContradictionJudgeApprox5Adapter._parse_contradiction_response("nope")

        with pytest.raises(ValueError, match="Invalid contradict"):
            ContradictionJudgeApprox5Adapter._parse_contradiction_response(
                '{"contradict": 2, "reason": "bad"}'
            )

    @pytest.mark.asyncio
    async def test_get_individual_result_no_contradiction(self):
        """contradict 0 maps to True, score 1.0, and keeps reason and claims."""
        fact = MockConnector(
            response_value=json.dumps(
                {"facts": ["Singapore's population is 5.92 million."]}
            )
        )
        judge = MockConnector(
            response_value=json.dumps(
                {
                    "contradict": 0,
                    "reason": "6 million is within ±5% of 5.92 million.",
                }
            )
        )
        entity = _entity()

        result = await _adapter(fact, judge).get_individual_result(entity)

        assert result["evaluated_response"] == "True"
        assert result["score"] == 1.0
        assert result["accuracy"] is True
        assert result["contradict"] == 0
        assert result["reason"] == "6 million is within ±5% of 5.92 million."
        assert result["ground_truth_facts"] == [
            "Singapore's population is 5.92 million."
        ]
        assert result["prompt"] == entity.prompt
        assert result["predicted_value"] == "About 6 million."
        assert result["target"] == entity.target
        assert "Singapore's population is 5.92 million." in fact.calls[0]
        assert fact.calls[0].startswith(
            ContradictionJudgeApprox5Adapter.FACT_EXTRACTION_PROMPT_TEMPLATE.split(
                "{text}"
            )[0]
        )
        assert (
            "Question:\nWhat is Singapore's population?" in result["evaluated_prompt"]
        )
        assert "- Singapore's population is 5.92 million." in result["evaluated_prompt"]
        assert "Assistant response:\nAbout 6 million." in result["evaluated_prompt"]

    @pytest.mark.asyncio
    async def test_get_individual_result_contradiction(self):
        """contradict 1 maps to False and score 0.0."""
        fact = MockConnector(response_value='{"facts": ["The year is 1965."]}')
        judge = MockConnector(
            response_value=json.dumps(
                {"contradict": 1, "reason": "1964 does not match 1965."}
            )
        )

        result = await _adapter(fact, judge).get_individual_result(_entity())

        assert result["evaluated_response"] == "False"
        assert result["score"] == 0.0
        assert result["accuracy"] is False
        assert result["contradict"] == 1
        assert result["reason"] == "1964 does not match 1965."
        assert result["ground_truth_facts"] == ["The year is 1965."]

    @pytest.mark.asyncio
    async def test_fenced_judge_json(self):
        """A markdown fence around the judge JSON still scores."""
        fact = MockConnector(response_value='{"facts": ["One claim."]}')
        judge = MockConnector(
            response_value='```json\n{"contradict": 0, "reason": "Matches."}\n```'
        )

        result = await _adapter(fact, judge).get_individual_result(_entity())

        assert result["evaluated_response"] == "True"
        assert result["reason"] == "Matches."
        assert result["evaluated_raw_response"].startswith("```json")

    @pytest.mark.asyncio
    async def test_empty_target_skips_fact_extraction(self):
        """Whitespace ground truth skips extraction and judges with no claims."""
        fact = MockConnector(response_value='{"facts": ["should not be used"]}')
        judge = MockConnector(
            response_value='{"contradict": 0, "reason": "No claims to contradict."}'
        )

        result = await _adapter(fact, judge).get_individual_result(
            _entity(target="   ")
        )

        assert fact.calls == []
        assert result["ground_truth_facts"] == []
        assert "(none)" in result["evaluated_prompt"]
        assert result["evaluated_response"] == "True"
        assert "Ground truth claims:\n(none)" in judge.calls[0]

    @pytest.mark.asyncio
    async def test_empty_fact_reply_retries_once(self):
        """An empty fact-extraction reply is retried once."""
        fact = MockConnector()
        fact.responses = ["", '{"facts": ["Retried claim."]}']
        judge = MockConnector(
            response_value='{"contradict": 0, "reason": "Consistent."}'
        )

        result = await _adapter(fact, judge).get_individual_result(_entity())

        assert len(fact.calls) == 2
        assert result["ground_truth_facts"] == ["Retried claim."]
        assert len(judge.calls) == 1

    @pytest.mark.asyncio
    async def test_unparseable_facts_raise_without_judge_call(self):
        """Non-empty unparseable fact JSON raises and does not call the judge."""
        fact = MockConnector(response_value="not json")
        judge = MockConnector(response_value='{"contradict": 0, "reason": "unused"}')

        with pytest.raises(ValueError, match="fact extraction"):
            await _adapter(fact, judge).get_individual_result(_entity())

        assert len(fact.calls) == 1
        assert judge.calls == []

    @pytest.mark.asyncio
    async def test_bad_judge_json_raises(self):
        """Invalid judge JSON raises instead of returning a score."""
        fact = MockConnector(response_value='{"facts": ["A claim."]}')
        judge = MockConnector(response_value="I think it contradicts.")

        with pytest.raises(ValueError, match="contradiction judge"):
            await _adapter(fact, judge).get_individual_result(_entity())

    @pytest.mark.asyncio
    async def test_get_individual_result_invalid_entity(self):
        """Missing prompt or model response is rejected."""
        adapter = _adapter(MockConnector(), MockConnector())
        entity = MetricIndividualEntity(
            prompt="",
            predicted_result=ConnectorResponseEntity(response=""),
            target="ground truth",
            evaluated_result={},
        )

        with pytest.raises(ValueError, match="Invalid entity"):
            await adapter.get_individual_result(entity)

    @pytest.mark.asyncio
    async def test_get_individual_result_no_connector(self):
        """A missing judge connector raises before any model call."""
        adapter = ContradictionJudgeApprox5Adapter.__new__(
            ContradictionJudgeApprox5Adapter
        )
        adapter.fact_connector = None
        adapter.judge_connector = None

        with pytest.raises(RuntimeError, match="No metric connector available"):
            await adapter.get_individual_result(_entity())

    @pytest.mark.asyncio
    async def test_get_results_no_contradiction_rate(self):
        """Aggregate rate is the percentage of True (no-contradiction) rows."""
        adapter = ContradictionJudgeApprox5Adapter.__new__(
            ContradictionJudgeApprox5Adapter
        )
        categories = ["True", "True", "False", "unknown"]
        entities = [
            MetricIndividualEntity(
                prompt=f"prompt {index}",
                predicted_result=ConnectorResponseEntity(response=f"R{index}"),
                target="gt",
                evaluated_result={"evaluated_response": category},
            )
            for index, category in enumerate(categories)
        ]

        result = await adapter.get_results(entities)

        assert result == {"ContradictionJudgeApprox5": {"no_contradiction_rate": 50.0}}

    @pytest.mark.asyncio
    async def test_get_results_empty_list(self):
        """An empty prompt list aggregates to a zero rate."""
        adapter = ContradictionJudgeApprox5Adapter.__new__(
            ContradictionJudgeApprox5Adapter
        )

        result = await adapter.get_results([])

        assert result == {"ContradictionJudgeApprox5": {"no_contradiction_rate": 0.0}}
