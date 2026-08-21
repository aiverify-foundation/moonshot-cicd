"""
Integration tests for the full "Seed Benchmark Run from YAML Bundle Config and JSON Dataset" flow.

Uses real DB, SharedConfigSeedService (with FileSharedConfigRepository, FileDatasetRepository,
BenchmarkDatasetSeedService, SqlAlchemyDatasetRepository), BenchmarkRunTestBundlePopulationService,
and BenchmarkRunTestSetupService. Fixtures: shared_minimal.yaml and test_sample_dataset.json.
"""

from pathlib import Path
from datetime import datetime, timezone

import pytest
import yaml
from sqlalchemy import text

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkTestDatasetModel,
    BenchmarkTestDatasetPromptModel,
    BenchmarkTestBundleModel,
    BenchmarkTestModel,
    BenchmarkTestBundleGroupingModel,
    BenchmarkRunModel,
    BenchmarkRunTestStatusModel,
    BenchmarkRunTestPromptModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from application.services.shared_config_seed_service import SharedConfigSeedService
from application.services.file_shared_config_repository import (
    FileSharedConfigRepository,
)
from application.services.file_dataset_repository import FileDatasetRepository
from application.services.benchmark_dataset_seed_service import (
    BenchmarkDatasetSeedService,
)
from application.services.benchmark_run_test_bundle_population_service import (
    BenchmarkRunTestBundlePopulationService,
)
from application.services.benchmark_run_test_setup_service import (
    BenchmarkRunTestSetupService,
)
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import (
    MoonshotConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.dataset_adapter import (
    SqlAlchemyDatasetRepository,
)


# Expected content from test_sample_dataset.json (data/datasets/)
EXPECTED_DATASET_DESCRIPTION = "Small Pokemon sample dataset solely for testing purposes."
EXPECTED_DATASET_LICENSE = ""
EXPECTED_DATASET_REFERENCE = ""
EXPECTED_EXAMPLES = [
    {"input": "How many dragon type moves are there in the first generation of pokemon? Give me a one-word answer.", "target": "One."},
    {"input": "What are the two moves that Magikarp can learn? Give me just the names of the moves.", "target": "Splash and Tackle."},
    {"input": "Which pokemon has the same base stats as Kyogre and Groundon? Give me a one-word answer.", "target": "Slaking."},
    {"input": "Which flying-type move is normal-type in R/B/Y? Give me a one-word answer.", "target": "Gust."},
    {"input": "Which move from R/B/Y became a HM in G/S/C? Give me a one-word answer.", "target": "Waterfall."},
]


@pytest.fixture(scope="function")
def test_db_path():
    """Temporary database path for integration tests."""
    moonshot_core_root = Path(__file__).resolve().parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_seed_benchmark_run.db"
    if db_path.exists():
        db_path.unlink()
    yield str(db_path)


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    """Set MOONSHOT_DB_PATH and reset SessionManager so migrations run on first use."""
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def config_path():
    """Path to minimal shared config that references only test_sample_dataset."""
    return (
        Path(__file__).resolve().parent
        / "fixtures"
        / "shared_minimal.yaml"
    )


@pytest.fixture
def shared_config_seed_service(test_db_env):
    """Build SharedConfigSeedService with full stack for seed_if_test_file_changed."""
    shared_config_repo = FileSharedConfigRepository()
    file_dataset_repo = FileDatasetRepository()
    moonshot_config = MoonshotConfigAdapter()
    sqlalchemy_dataset_repo = SqlAlchemyDatasetRepository()
    dataset_seed_service = BenchmarkDatasetSeedService(
        source_dataset_repository=file_dataset_repo,
        target_dataset_repository=sqlalchemy_dataset_repo,
    )
    return SharedConfigSeedService(
        moonshot_config_repository=moonshot_config,
        shared_config_repository=shared_config_repo,
        benchmark_dataset_seed_service=dataset_seed_service,
    )


def _insert_benchmark_run(session_manager, name: str, status: str = "not_started") -> int:
    """Insert a benchmark_run row via raw SQL; return the new run id."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with session_manager.get_session() as session:
        session.execute(
            text("""
                INSERT INTO benchmark_run (name, status, endpoint_type, start_time)
                VALUES (:name, :status, :endpoint_type, :start_time)
            """),
            {
                "name": name,
                "status": status,
                "endpoint_type": "LLM_Provider",
                "start_time": now,
            },
        )
        session.flush()
        (run_id,) = session.execute(text("SELECT last_insert_rowid()")).fetchone()
        return run_id


def _get_dataset_by_system_name(session_manager, system_name: str):
    """Return (id, system_name, description, license, reference) for system_name or None."""
    with session_manager.get_session() as session:
        row = (
            session.query(BenchmarkTestDatasetModel)
            .filter(BenchmarkTestDatasetModel.system_name == system_name)
            .first()
        )
        if row is None:
            return None
        return (row.id, row.system_name, row.description, row.license, row.reference)


def _get_dataset_prompts(session_manager, dataset_id: int):
    """Return list of (prompt, target) for the dataset."""
    with session_manager.get_session() as session:
        rows = (
            session.query(BenchmarkTestDatasetPromptModel)
            .filter(
                BenchmarkTestDatasetPromptModel.benchmark_test_dataset_id
                == dataset_id
            )
            .order_by(BenchmarkTestDatasetPromptModel.id)
            .all()
        )
        return [(r.prompt, r.target) for r in rows]


def _get_bundle_by_system_name(session_manager, system_name: str):
    """Return (id, system_name, name) for system_name or None."""
    with session_manager.get_session() as session:
        row = (
            session.query(BenchmarkTestBundleModel)
            .filter(BenchmarkTestBundleModel.system_name == system_name)
            .first()
        )
        if row is None:
            return None
        return (row.id, row.system_name, row.name)


def _count_run_test_status_by_run_id(session_manager, run_id: int) -> int:
    """Return number of benchmark_run_test_status rows for the given run_id."""
    with session_manager.get_session() as session:
        return (
            session.query(BenchmarkRunTestStatusModel)
            .filter(BenchmarkRunTestStatusModel.run_id == run_id)
            .count()
        )


def _get_run_test_statuses(session_manager, run_id: int):
    """Return list of (id, status, start_dt, end_dt) for the run."""
    with session_manager.get_session() as session:
        rows = (
            session.query(BenchmarkRunTestStatusModel)
            .filter(BenchmarkRunTestStatusModel.run_id == run_id)
            .all()
        )
        return [(r.id, r.status, r.start_dt, r.end_dt) for r in rows]


def _get_run_test_prompts(session_manager, run_test_id: int):
    """Return list of (prompt_id, target, prediction_result, evaluation_prediction_result, evaluation_accuracy)."""
    with session_manager.get_session() as session:
        rows = (
            session.query(BenchmarkRunTestPromptModel)
            .filter(BenchmarkRunTestPromptModel.run_test_id == run_test_id)
            .all()
        )
        return [
            (
                r.prompt_id,
                r.target,
                r.prediction_result,
                r.evaluation_prediction_result,
                r.evaluation_accuracy,
            )
            for r in rows
        ]


def _count_run_test_prompts_for_run(session_manager, run_id: int) -> int:
    """Return total number of benchmark_run_test_prompt rows for all statuses of this run."""
    statuses = _get_run_test_statuses(session_manager, run_id)
    total = 0
    for (status_id, _, _, _) in statuses:
        with session_manager.get_session() as session:
            total += (
                session.query(BenchmarkRunTestPromptModel)
                .filter(BenchmarkRunTestPromptModel.run_test_id == status_id)
                .count()
            )
    return total


def _get_run_status(session_manager, run_id: int):
    """Return (status,) for run_id or None."""
    with session_manager.get_session() as session:
        row = (
            session.query(BenchmarkRunModel)
            .filter(BenchmarkRunModel.id == run_id)
            .first()
        )
        return (row.status,) if row is not None else None


@pytest.mark.integration
class TestSeedBenchmarkRunBundleDatasetIntegration:
    """Integration tests for seed benchmark run from YAML bundle config and JSON dataset."""

    def test_benchmark_test_dataset_record_created_from_json(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
    ):
        """Seed benchmark_test_dataset from JSON file: record has system_name, description, license, reference."""
        assert config_path.exists()
        session_manager = SessionManager.get_instance()
        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert result is True

        row = _get_dataset_by_system_name(session_manager, "test_sample_dataset")
        assert row is not None
        assert row[1] == "test_sample_dataset"
        assert row[2] == EXPECTED_DATASET_DESCRIPTION
        assert (row[3] or "") == EXPECTED_DATASET_LICENSE
        assert (row[4] or "") == EXPECTED_DATASET_REFERENCE

    def test_benchmark_test_dataset_prompt_records_from_json_examples(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
    ):
        """Seed benchmark_test_dataset_prompt from JSON examples: input->prompt, target->target."""
        assert config_path.exists()
        session_manager = SessionManager.get_instance()
        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert result is True

        dataset_row = _get_dataset_by_system_name(
            session_manager, "test_sample_dataset"
        )
        assert dataset_row is not None
        dataset_id = dataset_row[0]
        prompts = _get_dataset_prompts(session_manager, dataset_id)
        assert len(prompts) == len(EXPECTED_EXAMPLES)

        expected_by_prompt = {e["input"]: e["target"] for e in EXPECTED_EXAMPLES}
        for (prompt, target) in prompts:
            assert prompt in expected_by_prompt
            assert target == expected_by_prompt[prompt]

    def test_benchmark_test_bundle_from_yaml_config(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
    ):
        """Seed benchmark_test_bundle from YAML config: bundle name from root key."""
        assert config_path.exists()
        session_manager = SessionManager.get_instance()
        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert result is True

        config = yaml.safe_load(config_path.read_text())
        bundle_key = "minimal-bundle"
        assert bundle_key in config
        expected_name = config[bundle_key].get("name", bundle_key)

        row = _get_bundle_by_system_name(session_manager, bundle_key)
        assert row is not None
        assert row[1] == bundle_key
        assert row[2] == expected_name

    def test_benchmark_test_records_from_yaml_tests(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
    ):
        """Seed benchmark_test from YAML test definition: name, type, dataset, metric resolved."""
        assert config_path.exists()
        session_manager = SessionManager.get_instance()
        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert result is True

        config_adapter = BenchmarkTestConfigAdapter()
        bundle_id = config_adapter.get_bundle_id_by_system_name_latest(
            "minimal-bundle"
        )
        assert bundle_id is not None
        test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
        config = yaml.safe_load(config_path.read_text())
        expected_tests = config["minimal-bundle"]["tests"]
        assert len(test_ids) == len(expected_tests)

        with session_manager.get_session() as session:
            for test_id in test_ids:
                test_row = (
                    session.query(BenchmarkTestModel)
                    .filter(BenchmarkTestModel.id == test_id)
                    .first()
                )
                assert test_row is not None
                assert test_row.name is not None
                assert test_row.type is not None
                assert test_row.dataset_id is not None

    def test_benchmark_test_bundle_grouping_links_tests_to_bundle(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
    ):
        """Link benchmark_test to benchmark_test_bundle via benchmark_test_bundle_grouping."""
        assert config_path.exists()
        session_manager = SessionManager.get_instance()
        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert result is True

        config_adapter = BenchmarkTestConfigAdapter()
        bundle_id = config_adapter.get_bundle_id_by_system_name_latest(
            "minimal-bundle"
        )
        test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
        config = yaml.safe_load(config_path.read_text())
        expected_count = len(config["minimal-bundle"]["tests"])

        with session_manager.get_session() as session:
            groupings = (
                session.query(BenchmarkTestBundleGroupingModel)
                .filter(
                    BenchmarkTestBundleGroupingModel.test_bundle_id == bundle_id
                )
                .all()
            )
            grouping_tuples = [(g.test_bundle_id, g.test_id) for g in groupings]
        assert len(grouping_tuples) == expected_count
        grouping_test_ids = {g[1] for g in grouping_tuples}
        assert grouping_test_ids == set(test_ids)

    def test_run_test_status_created_per_test_not_started_null_execution(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
    ):
        """Create empty benchmark_run_test_status for each test: status not_started, execution fields NULL."""
        assert config_path.exists()
        session_manager = SessionManager.get_instance()
        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert result is True

        run_id = _insert_benchmark_run(
            session_manager, "seed-integration-status-test", status="not_started"
        )
        pop_service = BenchmarkRunTestBundlePopulationService()
        pop_service.populate_run_bundle(run_id, "minimal-bundle")

        config_adapter = BenchmarkTestConfigAdapter()
        bundle_id = config_adapter.get_bundle_id_by_system_name_latest(
            "minimal-bundle"
        )
        test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
        setup_service = BenchmarkRunTestSetupService()
        for test_id in test_ids:
            setup_service.create_run_test_with_prompts(run_id, test_id)

        statuses = _get_run_test_statuses(session_manager, run_id)
        assert len(statuses) == len(test_ids)
        for (_id, status, start_dt, end_dt) in statuses:
            assert status == "not_started"
            assert start_dt is None
            assert end_dt is None

    def test_run_test_prompt_records_per_dataset_prompt_null_result_evaluation(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
    ):
        """Seed empty benchmark_run_test_prompt per dataset prompt: prompt_id/target set, result/evaluation NULL."""
        assert config_path.exists()
        session_manager = SessionManager.get_instance()
        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert result is True

        run_id = _insert_benchmark_run(
            session_manager, "seed-integration-prompts-test", status="not_started"
        )
        pop_service = BenchmarkRunTestBundlePopulationService()
        pop_service.populate_run_bundle(run_id, "minimal-bundle")

        config_adapter = BenchmarkTestConfigAdapter()
        test_ids = config_adapter.get_test_ids_by_bundle_id(
            config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
        )
        setup_service = BenchmarkRunTestSetupService()
        for test_id in test_ids:
            setup_service.create_run_test_with_prompts(run_id, test_id)

        statuses = _get_run_test_statuses(session_manager, run_id)
        assert len(statuses) == len(test_ids)
        for (status_id, _, _, _) in statuses:
            prompts = _get_run_test_prompts(session_manager, status_id)
            assert len(prompts) == len(EXPECTED_EXAMPLES)
            for (prompt_id, target, pred_result, eval_pred, eval_acc) in prompts:
                assert prompt_id is not None
                assert target is not None
                assert pred_result is None
                assert eval_pred is None
                assert eval_acc is None

    def test_full_seeding_flow_record_counts_and_run_status(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
    ):
        """Full seeding flow: one run_test_status per test, one run_test_prompt per example per test, run status not_started."""
        assert config_path.exists()
        session_manager = SessionManager.get_instance()

        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert result is True

        run_id = _insert_benchmark_run(
            session_manager, "seed-integration-full-flow", status="not_started"
        )
        pop_service = BenchmarkRunTestBundlePopulationService()
        pop_service.populate_run_bundle(run_id, "minimal-bundle")

        config_adapter = BenchmarkTestConfigAdapter()
        test_ids = config_adapter.get_test_ids_by_bundle_id(
            config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
        )
        config = yaml.safe_load(config_path.read_text())
        expected_test_count = len(config["minimal-bundle"]["tests"])
        expected_example_count = len(EXPECTED_EXAMPLES)

        setup_service = BenchmarkRunTestSetupService()
        for test_id in test_ids:
            setup_service.create_run_test_with_prompts(run_id, test_id)

        assert _count_run_test_status_by_run_id(
            session_manager, run_id
        ) == expected_test_count
        assert _count_run_test_prompts_for_run(
            session_manager, run_id
        ) == expected_test_count * expected_example_count

        run_row = _get_run_status(session_manager, run_id)
        assert run_row is not None
        assert run_row[0] == "not_started"
