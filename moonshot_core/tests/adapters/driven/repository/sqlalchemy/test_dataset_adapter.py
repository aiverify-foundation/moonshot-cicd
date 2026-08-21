"""Tests for SqlAlchemyDatasetRepository (get_prompts_by_dataset_id)."""

import pytest
from pathlib import Path

from adapters.driven.repository.sqlalchemy.dataset_adapter import (
    SqlAlchemyDatasetRepository,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkTestDatasetModel,
    BenchmarkTestDatasetPromptModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager


@pytest.fixture(scope="function")
def test_db_path():
    """Create a temporary database path for testing."""
    moonshot_core_root = (
        Path(__file__).parent.parent.parent.parent.parent.parent
    )
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest.db"
    if db_path.exists():
        db_path.unlink()
    yield str(db_path)


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    """Set up test database environment variable and reset SessionManager."""
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def dataset_repo(test_db_env):
    """Create SqlAlchemyDatasetRepository with real SessionManager."""
    return SqlAlchemyDatasetRepository()


def _insert_dataset(session_manager, system_name: str, version: int) -> int:
    """Insert a BenchmarkTestDatasetModel row and return its id."""
    with session_manager.get_session() as session:
        model = BenchmarkTestDatasetModel(
            system_name=system_name,
            version=version,
            description=None,
            license=None,
            reference=None,
        )
        session.add(model)
        session.flush()
        return model.id


def _insert_prompt(session_manager, dataset_id: int, prompt: str, target: str) -> int:
    """Insert a BenchmarkTestDatasetPromptModel row and return its id."""
    with session_manager.get_session() as session:
        model = BenchmarkTestDatasetPromptModel(
            benchmark_test_dataset_id=dataset_id,
            prompt=prompt,
            target=target,
        )
        session.add(model)
        session.flush()
        return model.id


class TestGetPromptsByDatasetId:
    """Tests for get_prompts_by_dataset_id."""

    def test_returns_empty_list_when_no_prompts(
        self, dataset_repo
    ):
        """Returns empty list when dataset has no prompts."""
        session_manager = dataset_repo.session_manager
        dataset_id = _insert_dataset(session_manager, "empty-ds", 1)

        result = dataset_repo.get_prompts_by_dataset_id(dataset_id)

        assert result == []

    def test_returns_prompts_with_id_prompt_target(
        self, dataset_repo
    ):
        """Returns list of entities with id, prompt, target for each dataset prompt."""
        session_manager = dataset_repo.session_manager
        dataset_id = _insert_dataset(session_manager, "ds-with-prompts", 1)
        id1 = _insert_prompt(
            session_manager, dataset_id, "What is 2+2?", "4"
        )
        id2 = _insert_prompt(
            session_manager, dataset_id, "What is 3+3?", "6"
        )

        result = dataset_repo.get_prompts_by_dataset_id(dataset_id)

        assert len(result) == 2
        by_id = {e.id: e for e in result}
        assert by_id[id1].prompt == "What is 2+2?" and by_id[id1].target == "4"
        assert by_id[id2].prompt == "What is 3+3?" and by_id[id2].target == "6"
        assert by_id[id1].benchmark_test_dataset_id == dataset_id
        assert by_id[id2].benchmark_test_dataset_id == dataset_id

    def test_returns_prompts_in_id_order(self, dataset_repo):
        """Returned prompts follow benchmark_test_dataset_prompt.id order."""
        session_manager = dataset_repo.session_manager
        dataset_id = _insert_dataset(session_manager, "ds-order", 1)
        id_first = _insert_prompt(
            session_manager, dataset_id, "first prompt", "first"
        )
        id_second = _insert_prompt(
            session_manager, dataset_id, "second prompt", "second"
        )

        result = dataset_repo.get_prompts_by_dataset_id(dataset_id)

        assert [e.id for e in result] == [id_first, id_second]
        assert [e.prompt for e in result] == ["first prompt", "second prompt"]
