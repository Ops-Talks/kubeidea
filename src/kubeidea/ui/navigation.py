"""Navigation rail for the main application window."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import flet as ft

# The on_change callback may be sync or async.
NavCallback = Callable[[int], None] | Callable[[int], Awaitable[None]]


def build_navigation(page: ft.Page, on_change: NavCallback) -> ft.NavigationRail:
    """Build the main navigation rail.

    Args:
        page: The Flet page instance.
        on_change: Callback invoked with the selected destination index.
            May be a regular function or a coroutine function.

    Returns:
        A configured NavigationRail control.
    """

    async def _on_destination_change(e: Any) -> None:
        result = on_change(e.control.selected_index)
        if asyncio.iscoroutine(result):
            await result

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
