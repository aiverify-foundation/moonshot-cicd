"""Unit tests for BenchmarkRunResultsExportService."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.services.benchmark_run_results_export_service import (
    BenchmarkRunResultsExportError,
    BenchmarkRunResultsExportService,
)
from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)
from domain.entities.connector_entity import ConnectorEntity


def _evaluated_result(prompt: str, response: str, category: str = "safe") -> str:
    return str(
        {
            "prompt": prompt,
            "predicted_value": response,
            "target": "t1",
            "accuracy": category == "safe",
            "evaluated_prompt": f"Agent: {response}",
            "evaluated_response": category,
            "evaluated_raw_response": category,
            "score": 1.0 if category == "safe" else 0.0,
        }
    )


def _completed_run(**overrides) -> BenchmarkRunEntity:
    start = datetime(2026, 6, 10, 14, 4, 11, tzinfo=timezone.utc)
    end = datetime(2026, 6, 10, 14, 6, 58, tzinfo=timezone.utc)
    defaults = {
        "id": 1,
        "name": "my-sample-run-3",
        "status": "completed",
        "endpoint_type": "LLM_Provider",
        "start_time": start,
        "end_time": end,
        "llm_provider_id": 1,
        "llm_provider_model_id": 2,
        "llm_provider_model_config_id": 3,
    }
    defaults.update(overrides)
    return BenchmarkRunEntity(**defaults)


def _prompt_row(
    *,
    run_test_id: int,
    prompt_id: int,
    prompt: str,
    response: str,
) -> BenchmarkRunTestPromptEntity:
    return BenchmarkRunTestPromptEntity(
        id=prompt_id,
        run_test_id=run_test_id,
        prompt_id=prompt_id,
        status="completed",
        target="t1",
        prompt_additional_info=prompt,
        prediction_result=response,
        evaluation_prediction_result=_evaluated_result(prompt, response),
    )


@pytest.fixture
def service():
    return BenchmarkRunResultsExportService()


class TestExportRun:
    @patch(
        "application.services.benchmark_run_results_export_service."
        "DatabaseConnectorConfigService"
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkRunService"
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "SqlAlchemyBenchmarkRunTestStatusRepository"
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkRunPromptService"
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkTestConfigAdapter"
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkRunResultsExportService._get_test_type",
        return_value="benchmark",
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkRunResultsExportService._compute_evaluation_summary",
        new_callable=AsyncMock,
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "categorise_prompt_dicts",
        side_effect=lambda prompt_dicts, metric_name: {"safe": prompt_dicts},
    )
    def test_single_test_export(
        self,
        mock_categorise,
        mock_compute_summary,
        _mock_test_type,
        mock_config_adapter_class,
        mock_prompt_service_class,
        mock_status_repo_class,
        mock_run_service_class,
        mock_connector_service_class,
        service,
    ):
        run = _completed_run()
        mock_run_service_class.return_value.get_run_by_id.return_value = run

        status = BenchmarkRunTestStatusEntity(
            id=100,
            run_id=1,
            test_id=20,
            status="completed",
            start_dt=run.start_time,
            end_dt=run.end_time,
        )
        mock_status_repo_class.return_value.get_all_by_run_id.return_value = [status]

        prompts = [
            _prompt_row(
                run_test_id=100,
                prompt_id=1,
                prompt="prompt one",
                response="response one",
            )
        ]
        mock_prompt_service_class.return_value.get_all_prompts_by_run_id.return_value = (
            prompts
        )

        mock_config_adapter_class.return_value.get_test_info.return_value = (
            "MLCommons AILuminate - Legal Advice",
            "mlc-ailuminate-spc-lgl",
            "llamaguardannotator_adapter",
        )

        mock_connector_service_class.return_value.build_connector_entity.return_value = (
            ConnectorEntity(
                connector_adapter="openai_adapter",
                model="gpt-4o-mini",
                model_endpoint="",
                params={"api_key": "secret-key"},
            )
        )

        mock_compute_summary.return_value = {"Safety": {"safe_rate": 100.0}}

        payload = service.export_run(1, redact_secrets=True)

        assert payload is not None
        assert payload["run_metadata"]["run_id"] == "my-sample-run-3"
        assert payload["run_metadata"]["test_id"] == "my-sample-run-3"
        assert len(payload["run_results"]) == 1
        entry = payload["run_results"][0]
        assert entry["metadata"]["test_name"] == "MLCommons AILuminate - Legal Advice"
        assert entry["metadata"]["dataset"] == "mlc-ailuminate-spc-lgl"
        assert entry["metadata"]["connector"]["params"]["api_key"] == ""
        assert "safe" in entry["results"]["individual_results"]

    @patch(
        "application.services.benchmark_run_results_export_service."
        "DatabaseConnectorConfigService"
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkRunService"
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "SqlAlchemyBenchmarkRunTestStatusRepository"
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkRunPromptService"
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkTestConfigAdapter"
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkRunResultsExportService._get_test_type",
        return_value="benchmark",
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkRunResultsExportService._compute_evaluation_summary",
        new_callable=AsyncMock,
    )
    @patch(
        "application.services.benchmark_run_results_export_service."
        "categorise_prompt_dicts",
        side_effect=lambda prompt_dicts, metric_name: {"safe": prompt_dicts},
    )
    def test_multi_test_export(
        self,
        _mock_categorise,
        mock_compute_summary,
        _mock_test_type,
        mock_config_adapter_class,
        mock_prompt_service_class,
        mock_status_repo_class,
        mock_run_service_class,
        mock_connector_service_class,
        service,
    ):
        run = _completed_run()
        mock_run_service_class.return_value.get_run_by_id.return_value = run

        status1 = BenchmarkRunTestStatusEntity(
            id=100,
            run_id=1,
            test_id=20,
            status="completed",
            start_dt=run.start_time,
            end_dt=run.end_time,
        )
        status2 = BenchmarkRunTestStatusEntity(
            id=101,
            run_id=1,
            test_id=21,
            status="completed",
            start_dt=run.start_time,
            end_dt=run.end_time,
        )
        mock_status_repo_class.return_value.get_all_by_run_id.return_value = [
            status1,
            status2,
        ]

        prompts = [
            _prompt_row(
                run_test_id=100,
                prompt_id=1,
                prompt="vcr prompt",
                response="vcr response",
            ),
            _prompt_row(
                run_test_id=101,
                prompt_id=1,
                prompt="ncr prompt",
                response="ncr response",
            ),
        ]
        mock_prompt_service_class.return_value.get_all_prompts_by_run_id.return_value = (
            prompts
        )

        mock_config_adapter_class.return_value.get_test_info.side_effect = [
            ("MLCommons AILuminate - Violent Crimes", "mlc-ailuminate-vcr", "llamaguardannotator_adapter"),
            ("MLCommons AILuminate - Non Violent Crimes", "mlc-ailuminate-ncr", "llamaguardannotator_adapter"),
        ]

        mock_connector_service_class.return_value.build_connector_entity.return_value = (
            ConnectorEntity(
                connector_adapter="openai_adapter",
                model="gpt-4o-mini",
                model_endpoint="",
                params={},
            )
        )

        mock_compute_summary.return_value = {"Safety": {"safe_rate": 100.0}}

        payload = service.export_run(1)

        assert payload is not None
        assert payload["run_metadata"]["test_id"] == payload["run_metadata"]["run_id"]
        assert len(payload["run_results"]) == 2
        test_names = {entry["metadata"]["test_name"] for entry in payload["run_results"]}
        assert test_names == {
            "MLCommons AILuminate - Violent Crimes",
            "MLCommons AILuminate - Non Violent Crimes",
        }
        datasets = {entry["metadata"]["dataset"] for entry in payload["run_results"]}
        assert datasets == {"mlc-ailuminate-vcr", "mlc-ailuminate-ncr"}

    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkRunService"
    )
    def test_returns_none_when_run_missing(self, mock_run_service_class, service):
        mock_run_service_class.return_value.get_run_by_id.return_value = None
        assert service.export_run(999) is None

    @patch(
        "application.services.benchmark_run_results_export_service."
        "BenchmarkRunService"
    )
    def test_raises_when_run_not_completed(self, mock_run_service_class, service):
        mock_run_service_class.return_value.get_run_by_id.return_value = _completed_run(
            status="running"
        )
        with pytest.raises(BenchmarkRunResultsExportError, match="not completed"):
            service.export_run(1)
