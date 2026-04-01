"""Tests for kubeidea.ui.views.settings module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kubeidea.config.settings import AppSettings
from kubeidea.ui.views.settings import SettingsView


@pytest.fixture()
def mock_page() -> MagicMock:
    """Create a mock Flet page."""
    page = MagicMock()
    page.theme_mode = None
    page.theme = None
    page.update = MagicMock()
    page.controls = []
    return page


@pytest.fixture()
def settings_dir(tmp_path: Path) -> Path:
    """Temporary directory for settings persistence."""
    return tmp_path


class TestSettingsView:
    """Tests for the SettingsView class."""

    def test_init_loads_defaults(self, mock_page: MagicMock) -> None:
        """SettingsView should initialise with default settings."""
        with patch.object(AppSettings, "load", return_value=AppSettings()):
            view = SettingsView(mock_page)

        assert view._settings.theme_dark is True
        assert view._settings.language == "en-US"
        assert view._settings.telemetry_enabled is False
        assert view._theme_switch.value is True
        assert view._telemetry_switch.value is False

    def test_init_loads_saved_settings(self, mock_page: MagicMock) -> None:
        """SettingsView should load previously saved settings."""
        saved = AppSettings(
            theme_dark=False,
            language="pt-BR",
            telemetry_enabled=True,
            kubeconfig_path="/custom/kubeconfig",
        )
        with patch.object(AppSettings, "load", return_value=saved):
            view = SettingsView(mock_page)

        assert view._settings.theme_dark is False
        assert view._theme_switch.value is False
        assert view._language_dropdown.value == "pt-BR"
        assert view._telemetry_switch.value is True
        assert view._kubeconfig_field.value == "/custom/kubeconfig"

    def test_theme_toggle_applies_immediately(
        self,
        mock_page: MagicMock,
    ) -> None:
        """Toggling theme should call apply_theme immediately."""
        with patch.object(AppSettings, "load", return_value=AppSettings()):
            view = SettingsView(mock_page)

        with patch("kubeidea.ui.views.settings.apply_theme") as mock_apply:
            view._theme_switch.value = False
            view._on_theme_toggle(None)

            mock_apply.assert_called_once_with(mock_page, dark=False)
            assert view._settings.theme_dark is False
            assert view._has_unsaved_changes is True

    def test_language_change_marks_dirty(self, mock_page: MagicMock) -> None:
        """Changing language should mark settings as dirty."""
        with patch.object(AppSettings, "load", return_value=AppSettings()):
            view = SettingsView(mock_page)

        view._language_dropdown.value = "pt-BR"
        view._on_language_change(None)

        assert view._settings.language == "pt-BR"
        assert view._has_unsaved_changes is True

    def test_kubeconfig_change_marks_dirty(
        self,
        mock_page: MagicMock,
    ) -> None:
        """Changing kubeconfig path should mark settings as dirty."""
        with patch.object(AppSettings, "load", return_value=AppSettings()):
            view = SettingsView(mock_page)

        view._kubeconfig_field.value = "/new/path"
        view._on_kubeconfig_change(None)

        assert view._settings.kubeconfig_path == "/new/path"
        assert view._has_unsaved_changes is True

    def test_telemetry_toggle_marks_dirty(
        self,
        mock_page: MagicMock,
    ) -> None:
        """Toggling telemetry should mark settings as dirty."""
        with patch.object(AppSettings, "load", return_value=AppSettings()):
            view = SettingsView(mock_page)

        view._telemetry_switch.value = True
        view._on_telemetry_toggle(None)

        assert view._settings.telemetry_enabled is True
        assert view._has_unsaved_changes is True

    def test_save_persists_settings(self, mock_page: MagicMock) -> None:
        """Save should persist settings and clear dirty flag."""
        with patch.object(AppSettings, "load", return_value=AppSettings()):
            view = SettingsView(mock_page)

        view._has_unsaved_changes = True

        with patch.object(AppSettings, "save") as mock_save:
            view._on_save(None)

            mock_save.assert_called_once()
            assert view._has_unsaved_changes is False
            assert "saved" in (view._status_text.value or "").lower()

    def test_save_handles_error(self, mock_page: MagicMock) -> None:
        """Save should show error message on failure."""
        with patch.object(AppSettings, "load", return_value=AppSettings()):
            view = SettingsView(mock_page)

        with patch.object(
            AppSettings,
            "save",
            side_effect=OSError("disk full"),
        ):
            view._on_save(None)

            assert "failed" in (view._status_text.value or "").lower()

    def test_reset_restores_defaults(self, mock_page: MagicMock) -> None:
        """Reset should restore all fields to defaults."""
        custom = AppSettings(
            theme_dark=False,
            language="pt-BR",
            telemetry_enabled=True,
            kubeconfig_path="/custom",
        )
        with patch.object(AppSettings, "load", return_value=custom):
            view = SettingsView(mock_page)

        with patch("kubeidea.ui.views.settings.apply_theme"):
            view._on_reset(None)

        assert view._settings.theme_dark is True
        assert view._theme_switch.value is True
        assert view._language_dropdown.value == "en-US"
        assert view._telemetry_switch.value is False
        assert "config" in (view._kubeconfig_field.value or "").lower()
        assert view._has_unsaved_changes is True

    def test_save_round_trip(
        self,
        mock_page: MagicMock,
        settings_dir: Path,
    ) -> None:
        """Settings should survive save → load round-trip."""
        with patch.object(AppSettings, "load", return_value=AppSettings()):
            view = SettingsView(mock_page)

        view._settings.language = "pt-BR"
        view._settings.theme_dark = False
        view._settings.save(config_dir=settings_dir)

        loaded = AppSettings.load(config_dir=settings_dir)
        assert loaded.language == "pt-BR"
        assert loaded.theme_dark is False
