"""Unit tests for BenchmarkRunTestSetupService."""

from unittest.mock import MagicMock

import pytest

from application.services.benchmark_run_test_setup_service import (
    BenchmarkRunTestSetupService,
)
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)
from domain.entities.benchmark_test_dataset_prompt_entity import (
    BenchmarkTestDatasetPromptEntity,
)


@pytest.fixture
def mock_status_service():
    return MagicMock()


@pytest.fixture
def mock_prompt_repo():
    return MagicMock()


@pytest.fixture
def mock_config():
    return MagicMock()


@pytest.fixture
def mock_dataset_repo():
    return MagicMock()


@pytest.fixture
def mock_status_repo():
    return MagicMock()


@pytest.fixture
def service(
    mock_status_service,
    mock_status_repo,
    mock_prompt_repo,
    mock_config,
    mock_dataset_repo,
):
    mock_status_repo.get_by_run_and_test.return_value = None  # no existing
    return BenchmarkRunTestSetupService(
        status_service=mock_status_service,
        status_repository=mock_status_repo,
        prompt_repository=mock_prompt_repo,
        config_adapter=mock_config,
        dataset_repository=mock_dataset_repo,
    )


class TestCreateRunTestWithPrompts:
    """Tests for create_run_test_with_prompts."""

    def test_creates_status_and_prompts_with_target_and_prompt_filled(
        self,
        service,
        mock_status_service,
        mock_prompt_repo,
        mock_config,
        mock_dataset_repo,
    ):
        """Creates one run test status and one run test prompt per dataset prompt; target and prompt filled."""
        mock_config.get_test_dataset_id.return_value = 7
        mock_dataset_repo.get_prompts_by_dataset_id.return_value = [
            BenchmarkTestDatasetPromptEntity(
                id=1,
                benchmark_test_dataset_id=7,
                prompt="What is 2+2?",
                target="4",
            ),
            BenchmarkTestDatasetPromptEntity(
                id=2,
                benchmark_test_dataset_id=7,
                prompt="What is 3+3?",
                target="6",
            ),
        ]
        saved_status = BenchmarkRunTestStatusEntity(
            id=100,
            run_id=10,
            test_id=20,
            status="not_started",
        )
        mock_status_service.save_run_test_status.return_value = saved_status

        def _save_echo(entity):
            return BenchmarkRunTestPromptEntity(
                id=entity.run_test_id * 10 + entity.prompt_id,
                run_test_id=entity.run_test_id,
                prompt_id=entity.prompt_id,
                status=entity.status,
                target=entity.target,
                prompt_additional_info=entity.prompt_additional_info,
            )

        mock_prompt_repo.save.side_effect = _save_echo

        status_result, prompts_result = service.create_run_test_with_prompts(
            benchmark_run_id=10,
            benchmark_test_id=20,
        )

        assert status_result.id == 100
        assert status_result.run_id == 10
        assert status_result.test_id == 20
        assert status_result.status == "not_started"

        mock_config.get_test_dataset_id.assert_called_once_with(20)
        mock_dataset_repo.get_prompts_by_dataset_id.assert_called_once_with(7)
        mock_status_service.save_run_test_status.assert_called_once()
        call_status = mock_status_service.save_run_test_status.call_args[0][0]
        assert call_status.run_id == 10
        assert call_status.test_id == 20
        assert call_status.status == "not_started"

        assert len(prompts_result) == 2
        assert mock_prompt_repo.save.call_count == 2
        call1 = mock_prompt_repo.save.call_args_list[0][0][0]
        call2 = mock_prompt_repo.save.call_args_list[1][0][0]
        assert call1.run_test_id == 100 and call1.prompt_id == 1
        assert call1.target == "4" and call1.prompt_additional_info == "What is 2+2?"
        assert call2.run_test_id == 100 and call2.prompt_id == 2
        assert call2.target == "6" and call2.prompt_additional_info == "What is 3+3?"

    def test_creates_status_and_zero_prompts_when_dataset_empty(
        self,
        service,
        mock_status_service,
        mock_prompt_repo,
        mock_config,
        mock_dataset_repo,
    ):
        """When dataset has no prompts, only run test status is created."""
        mock_config.get_test_dataset_id.return_value = 7
        mock_dataset_repo.get_prompts_by_dataset_id.return_value = []
        saved_status = BenchmarkRunTestStatusEntity(
            id=100,
            run_id=10,
            test_id=20,
            status="not_started",
        )
        mock_status_service.save_run_test_status.return_value = saved_status

        status_result, prompts_result = service.create_run_test_with_prompts(
            benchmark_run_id=10,
            benchmark_test_id=20,
        )

        assert status_result.id == 100
        assert len(prompts_result) == 0
        mock_prompt_repo.save.assert_not_called()

    def test_raises_when_test_not_found(self, service, mock_config):
        """Propagates ValueError when config raises (test not found)."""
        mock_config.get_test_dataset_id.side_effect = ValueError(
            "Benchmark test not found: test_id=999"
        )

        with pytest.raises(ValueError, match="Benchmark test not found"):
            service.create_run_test_with_prompts(
                benchmark_run_id=1,
                benchmark_test_id=999,
            )

    def test_returns_existing_when_run_test_already_exists(
        self,
        service,
        mock_status_service,
        mock_status_repo,
        mock_prompt_repo,
        mock_config,
        mock_dataset_repo,
    ):
        """When (run_id, test_id) already exists, returns existing status and prompts without creating."""
        existing_status = BenchmarkRunTestStatusEntity(
            id=100,
            run_id=10,
            test_id=20,
            status="not_started",
        )
        existing_prompts = [
            BenchmarkRunTestPromptEntity(
                id=1,
                run_test_id=100,
                prompt_id=1,
                status="pending",
                target="4",
            ),
        ]
        mock_status_repo.get_by_run_and_test.return_value = existing_status
        mock_prompt_repo.get_all_by_run_test_id.return_value = existing_prompts

        status_result, prompts_result = service.create_run_test_with_prompts(
            benchmark_run_id=10,
            benchmark_test_id=20,
        )

        assert status_result is existing_status
        assert status_result.id == 100
        assert prompts_result is existing_prompts
        assert len(prompts_result) == 1
        mock_status_repo.get_by_run_and_test.assert_called_once_with(10, 20)
        mock_prompt_repo.get_all_by_run_test_id.assert_called_once_with(100)
        mock_config.get_test_dataset_id.assert_not_called()
        mock_dataset_repo.get_prompts_by_dataset_id.assert_not_called()
        mock_status_service.save_run_test_status.assert_not_called()
        mock_prompt_repo.save.assert_not_called()
