"""Tests for start-benchmark-run request DTO validation."""

import pytest
from pydantic import ValidationError

from application.dto.run_bundle_dto import StartBenchmarkRunRequestDTO


def test_start_benchmark_run_request_accepts_tests_by_bundle():
    body = StartBenchmarkRunRequestDTO(
        bundle_names=["a", "b"],
        run_name="r",
        llm_provider_id=1,
        llm_provider_model_id=2,
        llm_provider_model_config_id=3,
        tests_by_bundle={"a": [10, 11]},
    )
    assert body.tests_by_bundle == {"a": [10, 11]}


def test_start_benchmark_run_request_rejects_tests_by_bundle_key_not_in_bundles():
    with pytest.raises(ValidationError, match="tests_by_bundle"):
        StartBenchmarkRunRequestDTO(
            bundle_names=["a"],
            run_name="r",
            llm_provider_id=1,
            llm_provider_model_id=2,
            llm_provider_model_config_id=3,
            tests_by_bundle={"unknown": [1]},
        )


def test_start_benchmark_run_request_rejects_empty_test_list_for_bundle():
    with pytest.raises(ValidationError, match="empty"):
        StartBenchmarkRunRequestDTO(
            bundle_names=["a"],
            run_name="r",
            llm_provider_id=1,
            llm_provider_model_id=2,
            llm_provider_model_config_id=3,
            tests_by_bundle={"a": []},
        )
