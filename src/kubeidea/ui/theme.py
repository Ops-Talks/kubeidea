"""Theme utilities for the Flet UI."""

import flet as ft


def apply_theme(page: ft.Page, dark: bool = True) -> None:
    """Apply theme settings to the page.

    Args:
        page: The Flet page instance.
        dark: Whether to use dark mode (default: True).
    """
    page.theme_mode = ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    page.update()
