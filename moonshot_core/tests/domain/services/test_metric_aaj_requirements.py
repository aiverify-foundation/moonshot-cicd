"""Tests for metric_aaj_requirements helper."""

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.metric_config_entity import MetricConfigEntity
from domain.services.metric_aaj_requirements import (
    AILUMINATE_JUDGE_CONNECTOR_SYSTEM_NAME,
    AILUMINATE_SAFETY_CLASSIFIER_METRIC,
    CYBERSEC_REFUSAL_METRIC,
    REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME,
    REFUSAL_METRIC,
    SG_FACT_CHECK_METRIC,
    SG_UC_CLASSIFIER_METRIC,
    SG_UC_JUDGE_CONNECTOR_SYSTEM_NAME,
    metric_aaj_fields,
    metric_grader_model_name,
)


def _fake_config(metric_name: str, adapter: str, model: str):
    class FakeConfig:
        def get_metric_config(self, name: str):
            if name != metric_name:
                return None
            return MetricConfigEntity(
                name=metric_name,
                connector_configurations=ConnectorEntity(
                    connector_adapter=adapter,
                    model=model,
                ),
                params={},
            )

    return FakeConfig()


def test_ailuminate_safety_classifier_metric_sets_aaj():
    requires, provider = metric_aaj_fields(
        {"name": AILUMINATE_SAFETY_CLASSIFIER_METRIC},
        app_config=_fake_config(
            AILUMINATE_SAFETY_CLASSIFIER_METRIC,
            AILUMINATE_JUDGE_CONNECTOR_SYSTEM_NAME,
            "gpt-5-mini",
        ),
    )
    assert requires is True
    assert provider == AILUMINATE_JUDGE_CONNECTOR_SYSTEM_NAME


def test_sg_uc_classifier_metric_sets_aaj():
    requires, provider = metric_aaj_fields(
        {"name": SG_UC_CLASSIFIER_METRIC},
        app_config=_fake_config(
            SG_UC_CLASSIFIER_METRIC,
            SG_UC_JUDGE_CONNECTOR_SYSTEM_NAME,
            "openai/gpt-oss-safeguard-20b",
        ),
    )
    assert requires is True
    assert provider == SG_UC_JUDGE_CONNECTOR_SYSTEM_NAME


def test_sg_uc_classifier_metric_prefers_config_adapter():
    requires, provider = metric_aaj_fields(
        {"name": SG_UC_CLASSIFIER_METRIC},
        app_config=_fake_config(
            SG_UC_CLASSIFIER_METRIC, "openrouter_adapter", "openai/gpt-oss-safeguard-20b"
        ),
    )
    assert requires is True
    assert provider == "openrouter_adapter"


def test_sg_fact_check_metric_sets_aaj():
    requires, provider = metric_aaj_fields(
        {"name": SG_FACT_CHECK_METRIC},
        app_config=_fake_config(
            SG_FACT_CHECK_METRIC, REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME, "gpt-4o"
        ),
    )
    assert requires is True
    assert provider == REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME


def test_refusal_metric_sets_aaj_and_openai():
    requires, provider = metric_aaj_fields(
        {"name": REFUSAL_METRIC},
        app_config=_fake_config(
            REFUSAL_METRIC, REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME, "gpt-4o"
        ),
    )
    assert requires is True
    assert provider == REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME


def test_cybersec_refusal_metric_sets_aaj_and_openai():
    requires, provider = metric_aaj_fields(
        {"name": CYBERSEC_REFUSAL_METRIC},
        app_config=_fake_config(
            CYBERSEC_REFUSAL_METRIC, REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME, "gpt-4o"
        ),
    )
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
    assert (
        metric_grader_model_name(
            {"name": REFUSAL_METRIC},
            app_config=_fake_config(REFUSAL_METRIC, "openai_adapter", "gpt-4o"),
        )
        == "gpt-4o"
    )


def test_metric_grader_model_name_empty_when_no_model():
    assert (
        metric_grader_model_name(
            {"name": "accuracy_adapter"},
            app_config=_fake_config("accuracy_adapter", "", ""),
        )
        is None
    )


def test_metric_grader_model_name_none_for_missing_metric():
    assert metric_grader_model_name(None) is None
    assert metric_grader_model_name({}) is None
