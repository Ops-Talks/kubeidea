"""Navigation rail for the main application window."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft


def build_navigation(page: ft.Page, on_change: Callable[[int], None]) -> ft.NavigationRail:
    """Build the main navigation rail.

    Args:
        page: The Flet page instance.
        on_change: Callback invoked with the selected destination index.

    Returns:
        A configured NavigationRail control.
    """

    def _on_destination_change(e: Any) -> None:
        on_change(e.control.selected_index)

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.HOME, label="Home"),
            ft.NavigationRailDestination(icon=ft.Icons.CLOUD, label="Clusters"),
            ft.NavigationRailDestination(icon=ft.Icons.EXPLORE, label="Explorer"),
            ft.NavigationRailDestination(icon=ft.Icons.TERMINAL, label="Logs"),
            ft.NavigationRailDestination(icon=ft.Icons.MONITOR_HEART, label="Metrics"),
            ft.NavigationRailDestination(icon=ft.Icons.CODE, label="YAML"),
            ft.NavigationRailDestination(icon=ft.Icons.SECURITY, label="RBAC"),
            ft.NavigationRailDestination(icon=ft.Icons.EXTENSION, label="Plugins"),
            ft.NavigationRailDestination(icon=ft.Icons.SETTINGS, label="Settings"),
        ],
        on_change=_on_destination_change,
    )
    return rail
