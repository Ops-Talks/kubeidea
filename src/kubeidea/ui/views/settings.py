"""Settings view — user preferences with persistence."""

from __future__ import annotations

from typing import Any

import flet as ft

import kubeidea
from kubeidea.config.settings import AppSettings
from kubeidea.ui.theme import apply_theme


class SettingsView(ft.Column):
    """View for managing application settings with persistence."""

    def __init__(self, page: ft.Page) -> None:
        super().__init__(expand=True, spacing=0)
        self._page = page
        self._settings = AppSettings.load()
        self._has_unsaved_changes = False

        # ── controls ──────────────────────────────────────────────

        self._theme_switch = ft.Switch(
            label="Dark mode",
            value=self._settings.theme_dark,
            on_change=self._on_theme_toggle,
        )

        self._language_dropdown = ft.Dropdown(
            label="Language",
            width=250,
            value=self._settings.language,
            on_select=self._on_language_change,
            options=[
                ft.DropdownOption(key="en-US", text="English"),
                ft.DropdownOption(key="pt-BR", text="Português (Brasil)"),
            ],
        )

        self._kubeconfig_field = ft.TextField(
            label="Kubeconfig path",
            value=self._settings.kubeconfig_path,
            expand=True,
            text_size=13,
            on_change=self._on_kubeconfig_change,
        )

        self._telemetry_switch = ft.Switch(
            label="Enable anonymous usage telemetry",
            value=self._settings.telemetry_enabled,
            on_change=self._on_telemetry_toggle,
        )

        self._save_btn = ft.Button(
            content=ft.Text("Save settings"),
            icon=ft.Icons.SAVE,
            on_click=self._on_save,
        )

        self._reset_btn = ft.Button(
            content=ft.Text("Reset to defaults"),
            icon=ft.Icons.RESTORE,
            on_click=self._on_reset,
        )

        self._status_text = ft.Text("", size=12)

        # ── layout ────────────────────────────────────────────────

        self.controls = [
            ft.Container(
                content=ft.Text(
                    "Settings",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                padding=ft.Padding.only(left=30, right=30, top=20),
            ),
            ft.Container(
                content=ft.Text(
                    "Configure Kube-IDEA preferences.",
                    size=12,
                    color=ft.Colors.GREY_500,
                ),
                padding=ft.Padding.only(left=30, bottom=8),
            ),
            ft.Divider(),
            ft.Container(
                content=ft.ListView(
                    expand=True,
                    spacing=4,
                    padding=ft.Padding.only(left=30, right=30, top=16, bottom=16),
                    controls=[
                        self._section(
                            "Appearance",
                            ft.Icons.PALETTE,
                            [self._theme_switch],
                        ),
                        self._section(
                            "Language",
                            ft.Icons.LANGUAGE,
                            [self._language_dropdown],
                        ),
                        self._section(
                            "Kubernetes",
                            ft.Icons.CLOUD,
                            [
                                ft.Text(
                                    "Path to the kubeconfig file used for " "cluster connections.",
                                    size=12,
                                    color=ft.Colors.GREY_500,
                                ),
                                self._kubeconfig_field,
                            ],
                        ),
                        self._section(
                            "Telemetry",
                            ft.Icons.ANALYTICS,
                            [
                                ft.Text(
                                    "Help improve Kube-IDEA by sending "
                                    "anonymous usage statistics. "
                                    "No personal data is ever collected.",
                                    size=12,
                                    color=ft.Colors.GREY_500,
                                ),
                                self._telemetry_switch,
                            ],
                        ),
                        self._section(
                            "About",
                            ft.Icons.INFO,
                            [
                                ft.Text(
                                    f"Kube-IDEA v{kubeidea.__version__}",
                                    size=14,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text(
                                    "Kubernetes desktop IDE — explore "
                                    "clusters, stream logs, manage "
                                    "resources, and more.",
                                    size=12,
                                    color=ft.Colors.GREY_500,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.TextButton(
                                            content=ft.Text("GitHub"),
                                            icon=ft.Icons.OPEN_IN_NEW,
                                            url="https://github.com/ops-talks/kubeidea",
                                        ),
                                        ft.TextButton(
                                            content=ft.Text("Documentation"),
                                            icon=ft.Icons.MENU_BOOK,
                                            url="https://ops-talks.github.io/kubeidea/",
                                        ),
                                    ],
                                    spacing=8,
                                ),
                            ],
                        ),
                        # action buttons
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    self._save_btn,
                                    self._reset_btn,
                                    self._status_text,
                                ],
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=ft.Padding.only(top=16, bottom=24),
                        ),
                    ],
                ),
                expand=True,
            ),
        ]

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _section(
        title: str,
        icon: str,
        children: list[ft.Control],
    ) -> ft.Container:
        """Build a settings section card."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, size=20, color=ft.Colors.BLUE_200),
                            ft.Text(
                                title,
                                size=16,
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=1),
                    *children,
                ],
                spacing=10,
            ),
            padding=20,
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
            margin=ft.Margin.only(bottom=12),
        )

    def _mark_dirty(self) -> None:
        self._has_unsaved_changes = True
        self._status_text.value = "Unsaved changes"
        self._status_text.color = ft.Colors.ORANGE_400

    # ── callbacks ──────────────────────────────────────────────────

    def _on_theme_toggle(self, _e: Any) -> None:
        self._settings.theme_dark = self._theme_switch.value or False
        apply_theme(self._page, dark=self._settings.theme_dark)
        self._mark_dirty()

    def _on_language_change(self, _e: Any) -> None:
        if self._language_dropdown.value:
            self._settings.language = self._language_dropdown.value
            self._mark_dirty()
            self._page.update()

    def _on_kubeconfig_change(self, _e: Any) -> None:
        self._settings.kubeconfig_path = self._kubeconfig_field.value or ""
        self._mark_dirty()

    def _on_telemetry_toggle(self, _e: Any) -> None:
        self._settings.telemetry_enabled = self._telemetry_switch.value or False
        self._mark_dirty()

    def _on_save(self, _e: Any) -> None:
        try:
            self._settings.save()
            self._has_unsaved_changes = False
            self._status_text.value = "Settings saved ✓"
            self._status_text.color = ft.Colors.GREEN_400
        except Exception as exc:
            self._status_text.value = f"Save failed: {exc}"
            self._status_text.color = ft.Colors.RED_400
        self._page.update()

    def _on_reset(self, _e: Any) -> None:
        defaults = AppSettings()
        self._settings = defaults

        self._theme_switch.value = defaults.theme_dark
        self._language_dropdown.value = defaults.language
        self._kubeconfig_field.value = defaults.kubeconfig_path
        self._telemetry_switch.value = defaults.telemetry_enabled

        apply_theme(self._page, dark=defaults.theme_dark)
        self._mark_dirty()
        self._page.update()
