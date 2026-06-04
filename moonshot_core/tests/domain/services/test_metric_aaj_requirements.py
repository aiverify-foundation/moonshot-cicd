"""Tests for metric_aaj_requirements helper."""

from domain.services.metric_aaj_requirements import (
    CYBERSEC_REFUSAL_METRIC,
    LLAMAGUARD_ANNOTATOR_METRIC,
    LLAMAGUARD_JUDGE_CONNECTOR_SYSTEM_NAME,
    REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME,
    REFUSAL_METRIC,
    metric_aaj_fields,
    metric_grader_model_name,
)


def test_llamaguard_metric_sets_aaj_and_together():
    requires, provider = metric_aaj_fields({"name": LLAMAGUARD_ANNOTATOR_METRIC})
    assert requires is True
    assert provider == LLAMAGUARD_JUDGE_CONNECTOR_SYSTEM_NAME


def test_refusal_metric_sets_aaj_and_openai():
    requires, provider = metric_aaj_fields({"name": REFUSAL_METRIC})
    assert requires is True
    assert provider == REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME


def test_cybersec_refusal_metric_sets_aaj_and_openai():
    requires, provider = metric_aaj_fields({"name": CYBERSEC_REFUSAL_METRIC})
    assert requires is True
    assert provider == REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME


def test_empty_metric():
    requires, provider = metric_aaj_fields({})
    assert requires is False
    assert provider is None


def test_none_metric():
    requires, provider = metric_aaj_fields(None)
    assert requires is False
    assert provider is None


def test_metric_grader_model_name_from_app_config():
    class FakeConfig:
        def get_metric_config(self, metric_name: str):
            if metric_name == REFUSAL_METRIC:
                from domain.entities.connector_entity import ConnectorEntity
                from domain.entities.metric_config_entity import MetricConfigEntity

                return MetricConfigEntity(
                    name=REFUSAL_METRIC,
                    connector_configurations=ConnectorEntity(
                        connector_adapter="openai_adapter",
                        model="gpt-4o",
                    ),
                    params={},
                )
            return None

    assert metric_grader_model_name(
        {"name": REFUSAL_METRIC}, app_config=FakeConfig()
    ) == "gpt-4o"


def test_metric_grader_model_name_empty_when_no_model():
    class FakeConfig:
        def get_metric_config(self, metric_name: str):
            from domain.entities.connector_entity import ConnectorEntity
            from domain.entities.metric_config_entity import MetricConfigEntity

            return MetricConfigEntity(
                name=metric_name,
                connector_configurations=ConnectorEntity(
                    connector_adapter="",
                    model="",
                ),
                params={},
            )

    assert metric_grader_model_name(
        {"name": "accuracy_adapter"}, app_config=FakeConfig()
    ) is None


def test_metric_grader_model_name_none_for_missing_metric():
    assert metric_grader_model_name(None) is None
    assert metric_grader_model_name({}) is None
