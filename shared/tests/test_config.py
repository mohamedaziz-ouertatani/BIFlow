"""Tests for shared/config.py: settings loading from environment."""

from shared.config import get_settings


def test_get_settings_reads_database_url_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@somehost:5432/somedb")
    settings = get_settings()
    assert settings.database_url == "postgresql://x:y@somehost:5432/somedb"


def test_get_settings_defaults_database_url_when_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = get_settings()
    assert settings.database_url == "postgresql://biflow:biflow@localhost:5433/biflow"
