from pathlib import Path

from adapters.driven.repository.sqlalchemy.custom_app_adapter import CustomAppAdapter
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.custom_app_seed_service import CustomAppSeedService


def _test_db_path() -> Path:
    moonshot_core_root: Path = Path(__file__).parent.parent.parent.parent
    return moonshot_core_root / "data" / "database" / "moonshot_custom_app_seed_pytest.db"


def _get_app_names() -> list[str]:
    return [app.name for app in CustomAppAdapter().list_all()]


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
