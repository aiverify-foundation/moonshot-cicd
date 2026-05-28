"""Tests for metric_aaj_requirements helper."""

from domain.services.metric_aaj_requirements import (
    LLAMAGUARD_ANNOTATOR_METRIC,
    LLAMAGUARD_JUDGE_CONNECTOR_SYSTEM_NAME,
    REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME,
    REFUSAL_METRIC,
    metric_aaj_fields,
)


def test_llamaguard_metric_sets_aaj_and_together():
    requires, provider = metric_aaj_fields({"name": LLAMAGUARD_ANNOTATOR_METRIC})
    assert requires is True
    assert provider == LLAMAGUARD_JUDGE_CONNECTOR_SYSTEM_NAME


def test_refusal_metric_sets_aaj_and_openai():
    requires, provider = metric_aaj_fields({"name": REFUSAL_METRIC})
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
