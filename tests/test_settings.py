"""Tests for kubeidea.config.settings module."""

import json
from pathlib import Path

from kubeidea.config.settings import AppSettings


def test_default_settings() -> None:
    """AppSettings should have safe defaults."""
    settings = AppSettings()
    assert settings.theme_dark is True
    assert settings.language == "en-US"
    assert settings.telemetry_enabled is False


def test_save_and_load(tmp_path: Path) -> None:
    """Settings should round-trip through save/load."""
    settings = AppSettings(theme_dark=False, language="pt-BR", telemetry_enabled=False)
    settings.save(config_dir=tmp_path)

    loaded = AppSettings.load(config_dir=tmp_path)
    assert loaded.theme_dark is False
    assert loaded.language == "pt-BR"
    assert loaded.telemetry_enabled is False


def test_load_missing_file(tmp_path: Path) -> None:
    """Loading from a directory with no settings file should return defaults."""
    loaded = AppSettings.load(config_dir=tmp_path)
    assert loaded.theme_dark is True


def test_load_partial_file(tmp_path: Path) -> None:
    """Loading a partial settings file should fill in defaults."""
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"language": "pt-BR"}), encoding="utf-8")

    loaded = AppSettings.load(config_dir=tmp_path)
    assert loaded.language == "pt-BR"
    assert loaded.theme_dark is True  # default preserved
