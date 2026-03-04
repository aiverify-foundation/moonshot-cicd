"""
Integration tests for BenchmarkExecutionService.start_benchmark_run.

These tests exercise the full flow: BenchmarkRunEntity creation, BenchmarkRunService
save_run (mocked to avoid DB schema/migration dependency), and starting bundle processes.
They touch BenchmarkExecutionService, BenchmarkRunService, BenchmarkService (mocked),
and multiprocessing.Process (mocked). Only Process and bundle resolution are mocked
so no subprocess or config/dataset files are required.
"""

from unittest.mock import MagicMock, patch

import pytest

from application.dto.bundle_dto import BundleDTO
from application.services.benchmark_execution_service import BenchmarkExecutionService
from domain.entities.benchmark_run_entity import BenchmarkRunEntity


@pytest.fixture
def minimal_bundle_dto():
    """Minimal BundleDTO for get_bundle_by_id so we don't depend on config/dataset files."""
    return BundleDTO(
        id="test-bundle-1",
        name="Test Bundle",
        description="",
        category="",
        tests=[],
        prompt_count=0,
    )


@pytest.fixture
def mock_process():
    """Mock multiprocessing.Process so no real subprocess is started."""
    with patch(
        "application.services.benchmark_execution_service.multiprocessing.Process"
    ) as process_class:
        mock_proc = MagicMock()
        process_class.return_value = mock_proc
        yield process_class


@pytest.fixture
def mock_get_bundle(minimal_bundle_dto):
    """Mock BenchmarkService.get_bundle_by_id to return a minimal bundle."""
    with patch(
        "application.services.benchmark.BenchmarkService"
    ) as mock_bs_class:
        mock_bs = MagicMock()
        mock_bs.get_bundle_by_id.return_value = minimal_bundle_dto
        mock_bs_class.return_value = mock_bs
        yield mock_bs.get_bundle_by_id


@pytest.fixture
def mock_save_run():
    """Mock BenchmarkRunService.save_run to return a run entity with id, no real DB."""
    with patch(
        "application.services.benchmark_run_service.BenchmarkRunService"
    ) as mock_svc_class:
        mock_svc = MagicMock()
        run_id = 42

        def _save_run(entity):
            # Return entity with id set, as the real save would
            return BenchmarkRunEntity(
                id=run_id,
                name=entity.name,
                status=entity.status,
                endpoint_type=entity.endpoint_type,
                start_time=entity.start_time,
                end_time=entity.end_time,
                llm_provider_id=entity.llm_provider_id,
                llm_provider_model_id=entity.llm_provider_model_id,
                llm_provider_endpoint_config_id=entity.llm_provider_endpoint_config_id,
            )

        mock_svc.save_run.side_effect = _save_run
        mock_svc_class.return_value = mock_svc
        yield mock_svc.save_run


@pytest.mark.integration
class TestStartBenchmarkRunIntegration:
    """Integration tests for start_benchmark_run touching run service and execution service."""

    def test_start_benchmark_run_saves_run_and_starts_bundles(
        self,
        mock_process,
        mock_get_bundle,
        mock_save_run,
        minimal_bundle_dto,
    ):
        """
        start_benchmark_run creates a run entity, calls BenchmarkRunService.save_run,
        and starts a background process per bundle with the correct run_id.
        """
        run_name = "integration-test-run"
        bundle_names = ["bundle-a", "bundle-b"]
        llm_provider_name = "TestProvider"
        llm_provider_config_name = "test-config"

        service = BenchmarkExecutionService()
        service.start_benchmark_run(
            run_name=run_name,
            bundle_names=bundle_names,
            llm_provider_name=llm_provider_name,
            llm_provider_config_name=llm_provider_config_name,
        )

        # save_run was called once with the expected entity
        assert mock_save_run.call_count == 1
        (call_entity,) = mock_save_run.call_args[0]
        assert call_entity.name == run_name
        assert call_entity.status == "running"
        assert call_entity.endpoint_type == "LLM_Provider"
        assert call_entity.start_time is not None
        assert call_entity.id is None

        # Returned run_id is used for processes (we use the value from our mock)
        run_id = 42

        # get_bundle_by_id was called for each bundle name
        assert mock_get_bundle.call_count == 2
        mock_get_bundle.assert_any_call("bundle-a")
        mock_get_bundle.assert_any_call("bundle-b")

        # Process was started twice (once per bundle) with correct args
        assert mock_process.call_count == 2
        for call in mock_process.call_args_list:
            _, kwargs = call
            args = kwargs["args"]
            bundle_id, connector, passed_run_id = args[0], args[1], args[2]
            assert connector == llm_provider_config_name
            assert passed_run_id == run_id
            assert bundle_id == minimal_bundle_dto.id

    def test_start_benchmark_run_raises_when_bundle_not_found(
        self,
        mock_process,
        mock_save_run,
    ):
        """When get_bundle_by_id raises KeyError, start_benchmark_run propagates it."""
        with patch(
            "application.services.benchmark.BenchmarkService"
        ) as mock_bs_class:
            mock_bs = MagicMock()
            mock_bs.get_bundle_by_id.side_effect = KeyError("Bundle 'missing' not found")
            mock_bs_class.return_value = mock_bs

            service = BenchmarkExecutionService()
            with pytest.raises(KeyError, match="Bundle .* not found"):
                service.start_benchmark_run(
                    run_name="run",
                    bundle_names=["missing"],
                    llm_provider_name="P",
                    llm_provider_config_name="cfg",
                )

        # save_run was still called (run is created before iterating bundles)
        assert mock_save_run.call_count == 1
