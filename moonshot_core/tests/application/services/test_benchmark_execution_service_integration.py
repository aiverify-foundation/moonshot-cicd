"""
Integration tests for BenchmarkExecutionService.start_benchmark_run.

These tests exercise the full flow: BenchmarkRunEntity creation, BenchmarkRunService
save_run (mocked to avoid DB schema/migration dependency), and starting bundle processes.
BenchmarkTestConfigAdapter and BenchmarkRunTestBundlePopulationService are mocked so
no real DB rows are required. multiprocessing.Process is mocked so no subprocess runs.
DatabaseConnectorConfigService.build_connector_entity is mocked so no relational
connector rows are required.
"""

from unittest.mock import MagicMock, patch

import pytest

from application.services.benchmark_execution_service import (
    BenchmarkExecutionService,
    BenchmarkRunTestSelectionError,
)
from application.services.database_connector_config_service import DatabaseConnectorConfigService
from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.entities.connector_entity import ConnectorEntity


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
def mock_save_run():
    """Mock BenchmarkRunService.save_run to return a run entity with id, no real DB."""
    with patch(
        "application.services.benchmark_execution_service.BenchmarkRunService"
    ) as mock_svc_class:
        mock_svc = MagicMock()
        run_id = 42

        def _save_run(entity):
            return BenchmarkRunEntity(
                id=run_id,
                name=entity.name,
                status=entity.status,
                endpoint_type=entity.endpoint_type,
                start_time=entity.start_time,
                end_time=entity.end_time,
                llm_provider_id=entity.llm_provider_id,
                llm_provider_model_id=entity.llm_provider_model_id,
                llm_provider_model_config_id=entity.llm_provider_model_config_id,
            )

        mock_svc.save_run.side_effect = _save_run
        mock_svc_class.return_value = mock_svc
        yield mock_svc.save_run


@pytest.fixture
def stub_connector_entity():
    return ConnectorEntity(
        connector_adapter="mock_adapter",
        model="m",
        model_endpoint="",
        params={},
    )


@pytest.mark.integration
class TestStartBenchmarkRunIntegration:
    """Integration tests for start_benchmark_run touching run service and execution service."""

    def test_start_benchmark_run_saves_run_and_starts_bundles(
        self,
        mock_process,
        mock_save_run,
        stub_connector_entity,
    ):
        """
        start_benchmark_run creates a run entity, calls BenchmarkRunService.save_run,
        and starts a background process per bundle with DB id trio in Process args.
        """
        run_name = "integration-test-run"
        bundle_names = ["bundle-a", "bundle-b"]
        llm_provider_id = 10
        llm_provider_model_id = 20
        llm_provider_model_config_id = 30

        with patch(
            "application.services.benchmark_execution_service.BenchmarkRunTestBundlePopulationService"
        ) as mock_pop_class:
            mock_pop = MagicMock()
            mock_pop.populate_run_bundle.return_value = {
                "run_id": 42,
                "test_bundle_id": 1,
                "inserted_count": 0,
            }
            mock_pop_class.return_value = mock_pop

            with patch(
                "application.services.benchmark_execution_service.BenchmarkTestConfigAdapter"
            ) as mock_cfg_cls:
                mock_cfg = MagicMock()
                mock_cfg.get_bundle_id_by_system_name_latest.return_value = 1
                mock_cfg.get_test_ids_by_bundle_id.return_value = [101, 102]
                mock_cfg_cls.return_value = mock_cfg

                with patch.object(
                    DatabaseConnectorConfigService,
                    "build_connector_entity",
                    return_value=stub_connector_entity,
                ):
                    service = BenchmarkExecutionService()
                    service.start_benchmark_run(
                        run_name=run_name,
                        bundle_names=bundle_names,
                        llm_provider_id=llm_provider_id,
                        llm_provider_model_id=llm_provider_model_id,
                        llm_provider_model_config_id=llm_provider_model_config_id,
                    )

                assert mock_cfg.get_bundle_id_by_system_name_latest.call_count == 4
                mock_cfg.get_bundle_id_by_system_name_latest.assert_any_call("bundle-a")
                mock_cfg.get_bundle_id_by_system_name_latest.assert_any_call("bundle-b")
                assert mock_cfg.get_test_ids_by_bundle_id.call_count == 2

        assert mock_save_run.call_count == 1
        (call_entity,) = mock_save_run.call_args[0]
        assert call_entity.name == run_name
        assert call_entity.status == "running"
        assert call_entity.endpoint_type == "LLM_Provider"
        assert call_entity.start_time is not None
        assert call_entity.id is None
        assert call_entity.llm_provider_id == llm_provider_id
        assert call_entity.llm_provider_model_id == llm_provider_model_id
        assert call_entity.llm_provider_model_config_id == llm_provider_model_config_id

        run_id = 42
        assert mock_process.call_count == 2
        started_bundles = []
        for call in mock_process.call_args_list:
            _, kwargs = call
            args = kwargs["args"]
            (
                bundle_name,
                passed_run_id,
                skip_alembic,
                pid,
                mid,
                mcid,
                custom_app_id,
                custom_app_config_id,
                passed_test_ids,
                passed_prompts_by_test,
                passed_continue_on_test_failure,
            ) = args
            assert passed_run_id == run_id
            assert skip_alembic is True
            assert pid == llm_provider_id
            assert mid == llm_provider_model_id
            assert mcid == llm_provider_model_config_id
            assert custom_app_id is None
            assert custom_app_config_id is None
            assert passed_test_ids == [101, 102]
            assert passed_prompts_by_test is None
            assert passed_continue_on_test_failure is False
            started_bundles.append(bundle_name)
        assert started_bundles == bundle_names

    def test_start_benchmark_run_raises_when_bundle_not_found(
        self,
        mock_process,
        mock_save_run,
        stub_connector_entity,
    ):
        """When bundle is not in DB, resolution raises KeyError before save_run."""
        with patch(
            "application.services.benchmark_execution_service.BenchmarkTestConfigAdapter"
        ) as mock_cfg_cls:
            mock_cfg = MagicMock()
            mock_cfg.get_bundle_id_by_system_name_latest.side_effect = ValueError(
                "not found"
            )
            mock_cfg_cls.return_value = mock_cfg

            with patch.object(
                DatabaseConnectorConfigService,
                "build_connector_entity",
                return_value=stub_connector_entity,
            ):
                service = BenchmarkExecutionService()
                with pytest.raises(KeyError, match="Bundle with ID 'missing' not found"):
                    service.start_benchmark_run(
                        run_name="run",
                        bundle_names=["missing"],
                        llm_provider_id=1,
                        llm_provider_model_id=2,
                        llm_provider_model_config_id=3,
                    )

        assert mock_save_run.call_count == 0

    def test_start_benchmark_run_tests_by_bundle_subset_passes_test_ids_to_process(
        self,
        mock_process,
        mock_save_run,
        stub_connector_entity,
    ):
        """tests_by_bundle subset is passed to Process and populate_run_bundle."""
        with patch(
            "application.services.benchmark_execution_service.BenchmarkRunTestBundlePopulationService"
        ) as mock_pop_class:
            mock_pop = MagicMock()
            mock_pop.populate_run_bundle.return_value = {
                "run_id": 42,
                "test_bundle_id": 1,
                "inserted_count": 1,
            }
            mock_pop_class.return_value = mock_pop

            with patch(
                "application.services.benchmark_execution_service.BenchmarkTestConfigAdapter"
            ) as mock_cfg_cls:
                mock_cfg = MagicMock()
                mock_cfg.get_bundle_id_by_system_name_latest.return_value = 7
                mock_cfg.get_test_ids_by_bundle_id.return_value = [201, 202, 203]
                mock_cfg_cls.return_value = mock_cfg

                with patch.object(
                    DatabaseConnectorConfigService,
                    "build_connector_entity",
                    return_value=stub_connector_entity,
                ):
                    service = BenchmarkExecutionService()
                    service.start_benchmark_run(
                        run_name="subset-run",
                        bundle_names=["bundle-x"],
                        llm_provider_id=1,
                        llm_provider_model_id=2,
                        llm_provider_model_config_id=3,
                        tests_by_bundle={"bundle-x": [202, 203]},
                    )

                mock_pop.populate_run_bundle.assert_called_once_with(
                    42, "bundle-x", test_ids=[202, 203]
                )

        (_, kwargs) = mock_process.call_args
        args = kwargs["args"]
        assert args[8] == [202, 203]
        assert args[9] is None
        assert args[10] is False

    def test_start_benchmark_run_prompts_by_test_passes_map_to_process(
        self,
        mock_process,
        mock_save_run,
        stub_connector_entity,
    ):
        """prompts_by_test is passed to Process and validated against resolved test ids."""
        with patch(
            "application.services.benchmark_execution_service.BenchmarkRunTestBundlePopulationService"
        ) as mock_pop_class:
            mock_pop = MagicMock()
            mock_pop.populate_run_bundle.return_value = {
                "run_id": 42,
                "test_bundle_id": 1,
                "inserted_count": 1,
            }
            mock_pop_class.return_value = mock_pop

            with patch(
                "application.services.benchmark_execution_service.BenchmarkTestConfigAdapter"
            ) as mock_cfg_cls:
                mock_cfg = MagicMock()
                mock_cfg.get_bundle_id_by_system_name_latest.return_value = 7
                mock_cfg.get_test_ids_by_bundle_id.return_value = [201, 202]
                mock_cfg_cls.return_value = mock_cfg

                with patch.object(
                    DatabaseConnectorConfigService,
                    "build_connector_entity",
                    return_value=stub_connector_entity,
                ):
                    service = BenchmarkExecutionService()
                    service.start_benchmark_run(
                        run_name="limited-run",
                        bundle_names=["bundle-x"],
                        llm_provider_id=1,
                        llm_provider_model_id=2,
                        llm_provider_model_config_id=3,
                        prompts_by_test={201: 5, 202: 10},
                    )

        (_, kwargs) = mock_process.call_args
        args = kwargs["args"]
        assert args[9] == {201: 5, 202: 10}
        assert args[10] is False

    def test_start_benchmark_run_prompts_by_test_unknown_test_id(
        self,
        mock_process,
        mock_save_run,
        stub_connector_entity,
    ):
        with patch(
            "application.services.benchmark_execution_service.BenchmarkTestConfigAdapter"
        ) as mock_cfg_cls:
            mock_cfg = MagicMock()
            mock_cfg.get_bundle_id_by_system_name_latest.return_value = 1
            mock_cfg.get_test_ids_by_bundle_id.return_value = [10, 11]
            mock_cfg_cls.return_value = mock_cfg

            with patch.object(
                DatabaseConnectorConfigService,
                "build_connector_entity",
                return_value=stub_connector_entity,
            ):
                service = BenchmarkExecutionService()
                with pytest.raises(BenchmarkRunTestSelectionError, match="not in this run"):
                    service.start_benchmark_run(
                        run_name="bad",
                        bundle_names=["b1"],
                        llm_provider_id=1,
                        llm_provider_model_id=2,
                        llm_provider_model_config_id=3,
                        prompts_by_test={99: 5},
                    )

        assert mock_save_run.call_count == 0

    def test_start_benchmark_run_tests_by_bundle_unknown_test_id(
        self,
        mock_process,
        mock_save_run,
        stub_connector_entity,
    ):
        with patch(
            "application.services.benchmark_execution_service.BenchmarkTestConfigAdapter"
        ) as mock_cfg_cls:
            mock_cfg = MagicMock()
            mock_cfg.get_bundle_id_by_system_name_latest.return_value = 1
            mock_cfg.get_test_ids_by_bundle_id.return_value = [10, 11]
            mock_cfg_cls.return_value = mock_cfg

            with patch.object(
                DatabaseConnectorConfigService,
                "build_connector_entity",
                return_value=stub_connector_entity,
            ):
                service = BenchmarkExecutionService()
                with pytest.raises(BenchmarkRunTestSelectionError, match="not in this bundle"):
                    service.start_benchmark_run(
                        run_name="bad",
                        bundle_names=["b1"],
                        llm_provider_id=1,
                        llm_provider_model_id=2,
                        llm_provider_model_config_id=3,
                        tests_by_bundle={"b1": [99]},
                    )

        assert mock_save_run.call_count == 0
