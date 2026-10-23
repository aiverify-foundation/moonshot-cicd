"""Tests for metric_aaj_requirements helper."""

import logging

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.metric_config_entity import MetricConfigEntity
from domain.services.metric_aaj_requirements import (
    AILUMINATE_SAFETY_CLASSIFIER_METRIC,
    CONTRADICTION_JUDGE_APPROX5_METRIC,
    CYBERSEC_REFUSAL_METRIC,
    REFUSAL_METRIC,
    SG_FACT_CHECK_METRIC,
    SG_UC_CLASSIFIER_METRIC,
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


class _MissingConfig:
    def get_metric_config(self, name: str):
        return None


def test_ailuminate_safety_classifier_metric_sets_aaj():
    requires, provider = metric_aaj_fields(
        {"name": AILUMINATE_SAFETY_CLASSIFIER_METRIC},
        app_config=_fake_config(
            AILUMINATE_SAFETY_CLASSIFIER_METRIC,
            "openai_adapter",
            "gpt-5-mini",
        ),
    )
    assert requires is True
    assert provider == "openai_adapter"


def test_sg_uc_classifier_metric_sets_aaj():
    requires, provider = metric_aaj_fields(
        {"name": SG_UC_CLASSIFIER_METRIC},
        app_config=_fake_config(
            SG_UC_CLASSIFIER_METRIC,
            "openrouter_adapter",
            "openai/gpt-oss-safeguard-20b",
        ),
    )
    assert requires is True
    assert provider == "openrouter_adapter"


def test_sg_uc_classifier_metric_uses_config_adapter():
    requires, provider = metric_aaj_fields(
        {"name": SG_UC_CLASSIFIER_METRIC},
        app_config=_fake_config(
            SG_UC_CLASSIFIER_METRIC,
            "aws_bedrock_adapter",
            "openai/gpt-oss-safeguard-20b",
        ),
    )
    assert requires is True
    assert provider == "aws_bedrock_adapter"


def test_sg_fact_check_metric_sets_aaj():
    requires, provider = metric_aaj_fields(
        {"name": SG_FACT_CHECK_METRIC},
        app_config=_fake_config(SG_FACT_CHECK_METRIC, "openai_adapter", "gpt-4o"),
    )
    assert requires is True
    assert provider == "openai_adapter"


def test_refusal_metric_sets_aaj_and_openai():
    requires, provider = metric_aaj_fields(
        {"name": REFUSAL_METRIC},
        app_config=_fake_config(REFUSAL_METRIC, "openai_adapter", "gpt-4o"),
    )
    assert requires is True
    assert provider == "openai_adapter"


def test_contradiction_judge_approx5_metric_sets_aaj():
    requires, provider = metric_aaj_fields(
        {"name": CONTRADICTION_JUDGE_APPROX5_METRIC},
        app_config=_fake_config(
            CONTRADICTION_JUDGE_APPROX5_METRIC,
            "aws_bedrock_adapter",
            "openai.gpt-oss-20b-1:0",
        ),
    )
    assert requires is True
    assert provider == "aws_bedrock_adapter"


def test_cybersec_refusal_metric_sets_aaj_and_openai():
    requires, provider = metric_aaj_fields(
        {"name": CYBERSEC_REFUSAL_METRIC},
        app_config=_fake_config(CYBERSEC_REFUSAL_METRIC, "openai_adapter", "gpt-4o"),
    )
    assert requires is True
    assert provider == "openai_adapter"


def test_whitelisted_metric_without_config_hides_judge(caplog):
    with caplog.at_level(
        logging.WARNING, logger="domain.services.metric_aaj_requirements"
    ):
        requires, provider = metric_aaj_fields(
            {"name": REFUSAL_METRIC},
            app_config=_MissingConfig(),
        )
    assert requires is False
    assert provider is None
    assert REFUSAL_METRIC in caplog.text


def test_whitelisted_metric_with_blank_adapter_hides_judge(caplog):
    with caplog.at_level(
        logging.WARNING, logger="domain.services.metric_aaj_requirements"
    ):
        requires, provider = metric_aaj_fields(
            {"name": REFUSAL_METRIC},
            app_config=_fake_config(REFUSAL_METRIC, "  ", "gpt-4o"),
        )
    assert requires is False
    assert provider is None
    assert REFUSAL_METRIC in caplog.text


def test_non_whitelisted_metric_with_connector_is_not_aaj(caplog):
    with caplog.at_level(
        logging.WARNING, logger="domain.services.metric_aaj_requirements"
    ):
        requires, provider = metric_aaj_fields(
            {"name": "faithfulness_adapter"},
            app_config=_fake_config(
                "faithfulness_adapter",
                "langchain_openai_chatopenai_adapter",
                "gpt-4o-mini",
            ),
        )
    assert requires is False
    assert provider is None
    assert caplog.records == []


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
