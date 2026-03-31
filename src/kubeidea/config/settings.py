"""Application settings with persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

_DEFAULT_CONFIG_DIR = Path.home() / ".kubeidea"
_SETTINGS_FILE = "settings.json"


class AppSettings(BaseModel):
    """Persisted user preferences.

    Attributes:
        theme_dark: Whether dark mode is active.
        language: UI language code (e.g. ``"en-US"``, ``"pt-BR"``).
        telemetry_enabled: Opt-in telemetry flag (disabled by default).
        kubeconfig_path: Path to the kubeconfig file.
    """

    theme_dark: bool = True
    language: str = "en-US"
    telemetry_enabled: bool = False
    kubeconfig_path: str = str(Path.home() / ".kube" / "config")

    @classmethod
    def load(cls, config_dir: Path | None = None) -> AppSettings:
        """Load settings from disk.

        Args:
            config_dir: Directory containing the settings file.

        Returns:
            An ``AppSettings`` instance (defaults if file is missing).
        """
        directory = config_dir or _DEFAULT_CONFIG_DIR
        path = directory / _SETTINGS_FILE
        if path.exists():
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            return cls.model_validate(data)
        return cls()

    def save(self, config_dir: Path | None = None) -> None:
        """Persist settings to disk.

        Args:
            config_dir: Directory where the settings file will be stored.
        """
        directory = config_dir or _DEFAULT_CONFIG_DIR
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / _SETTINGS_FILE
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
