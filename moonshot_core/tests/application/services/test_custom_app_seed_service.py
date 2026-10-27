from pathlib import Path
from unittest.mock import MagicMock, patch

from adapters.driven.repository.sqlalchemy.custom_app_adapter import CustomAppAdapter
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.custom_app_seed_service import (
    AWS_BEDROCK_API_APP_NAME,
    CustomAppSeedService,
)
from domain.services.enums.feature_flag_names import FeatureFlagNames
from domain.services.feature_flags import FeatureFlags


def _test_db_path() -> Path:
    moonshot_core_root: Path = Path(__file__).parent.parent.parent.parent
    return moonshot_core_root / "data" / "database" / "moonshot_custom_app_seed_pytest.db"


def _get_app_names() -> list[str]:
    return [app.name for app in CustomAppAdapter().list_all()]


def _patch_moon803(enabled: bool):
    adapter = MagicMock()
    adapter.load_flags.return_value = {FeatureFlagNames.AIVET_OCT2026_MOON803: enabled}
    return patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    )


def test_seed_hardcoded_custom_apps_is_idempotent(monkeypatch):
    db_path = _test_db_path()
    if db_path.exists():
        db_path.unlink()

    monkeypatch.setenv("MOONSHOT_DB_PATH", str(db_path))
    SessionManager.reset_instance()
    try:
        seed_service = CustomAppSeedService(custom_app_repository=CustomAppAdapter())
        seed_service.seed_hardcoded_custom_apps()
        seed_service.seed_hardcoded_custom_apps()

        names = _get_app_names()
        assert "API Connector" in names
        assert names.count("API Connector") == 1
    finally:
        SessionManager.reset_instance()
        monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)
        if db_path.exists():
            db_path.unlink()


def test_does_not_seed_bedrock_custom_app_when_moon803_disabled(monkeypatch):
    FeatureFlags.reset()
    db_path = _test_db_path()
    if db_path.exists():
        db_path.unlink()

    monkeypatch.setenv("MOONSHOT_DB_PATH", str(db_path))
    SessionManager.reset_instance()
    try:
        with _patch_moon803(False):
            seed_service = CustomAppSeedService(custom_app_repository=CustomAppAdapter())
            seed_service.seed_hardcoded_custom_apps()

        names = _get_app_names()
        assert "API Connector" in names
        assert AWS_BEDROCK_API_APP_NAME not in names
    finally:
        FeatureFlags.reset()
        SessionManager.reset_instance()
        monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)
        if db_path.exists():
            db_path.unlink()


def test_seeds_bedrock_custom_app_when_moon803_enabled(monkeypatch):
    FeatureFlags.reset()
    db_path = _test_db_path()
    if db_path.exists():
        db_path.unlink()

    monkeypatch.setenv("MOONSHOT_DB_PATH", str(db_path))
    SessionManager.reset_instance()
    try:
        with _patch_moon803(True):
            seed_service = CustomAppSeedService(custom_app_repository=CustomAppAdapter())
            seed_service.seed_hardcoded_custom_apps()

        names = _get_app_names()
        assert AWS_BEDROCK_API_APP_NAME in names
        assert names.count(AWS_BEDROCK_API_APP_NAME) == 1
    finally:
        FeatureFlags.reset()
        SessionManager.reset_instance()
        monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)
        if db_path.exists():
            db_path.unlink()
