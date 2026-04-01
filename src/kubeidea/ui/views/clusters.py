"""Clusters view — kubeconfig context listing, selection, and connectivity check."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import flet as ft

from kubeidea.core.context import AppContext
from kubeidea.kube.client import KubeConfigManager, KubeContext

# The on_connected / on_disconnected callbacks may be sync or async.
ConnectionCallback = Callable[[], None] | Callable[[], Awaitable[None]] | None


class ClustersView(ft.Column):
    """View that lists kubeconfig contexts and lets the user connect to one."""

    def __init__(
        self,
        page: ft.Page,
        ctx: AppContext,
        on_connected: ConnectionCallback = None,
        on_disconnected: ConnectionCallback = None,
    ) -> None:
        super().__init__(expand=True, spacing=10)
        self._page = page
        self._ctx = ctx
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._manager = KubeConfigManager()
        self._contexts: list[KubeContext] = []

        # --- header ---
        self._header = ft.Text("Clusters", size=24, weight=ft.FontWeight.BOLD)
        self._status_text = ft.Text("", size=12, color=ft.Colors.GREY_500)
        self._refresh_btn = ft.IconButton(
            ft.Icons.REFRESH,
            tooltip="Refresh contexts",
            on_click=self._on_refresh,
        )

        # --- context list ---
        self._context_list = ft.ListView(expand=True, spacing=4, padding=10)

        # --- detail panel ---
        self._detail = ft.Container(
            content=ft.Text("Select a context to see details.", size=13, color=ft.Colors.GREY_500),
            padding=20,
        )

        self.controls = [
            ft.Container(
                content=ft.Row(
                    controls=[self._header, self._refresh_btn],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.Padding.only(left=30, right=30, top=20),
            ),
            ft.Container(
                content=self._status_text,
                padding=ft.Padding.only(left=30),
            ),
            ft.Divider(),
            ft.Row(
                controls=[
                    ft.Container(content=self._context_list, expand=2),
                    ft.VerticalDivider(width=1),
                    ft.Container(content=self._detail, expand=3),
                ],
                expand=True,
            ),
        ]

        # load on init
        self._load_contexts()

    # ── data ──────────────────────────────────────────────────────────

    def _load_contexts(self) -> None:
        self._contexts = self._manager.list_contexts()
        self._context_list.controls.clear()

        if not self._contexts:
            self._status_text.value = f"No contexts found in {self._manager.kubeconfig_path}"
            self._status_text.color = ft.Colors.ORANGE_400
            self._context_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.WARNING_AMBER, size=40, color=ft.Colors.ORANGE_400),
                            ft.Text("No kubeconfig contexts found.", size=14),
                            ft.Text(
                                f"Checked: {self._manager.kubeconfig_path}",
                                size=11,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    padding=40,
                )
            )
        else:
            self._status_text.value = f"{len(self._contexts)} context(s) found"
            self._status_text.color = ft.Colors.GREY_500
            for ctx in self._contexts:
                self._context_list.controls.append(self._build_context_tile(ctx))

        if self._page.controls:
            self._page.update()

    def _build_context_tile(self, ctx: KubeContext) -> ft.Container:
        is_active = ctx.name == self._ctx.current_context

        def on_tap(_e: Any, context: KubeContext = ctx) -> None:
            self._show_detail(context)

        def on_connect(_e: Any, context: KubeContext = ctx) -> None:
            self._page.run_task(self._connect, context)

        def on_disconnect(_e: Any) -> None:
            self._page.run_task(self._disconnect)

        action_btn = (
            ft.Button(
                content=ft.Text("Disconnect"),
                icon=ft.Icons.POWER_OFF,
                on_click=on_disconnect,
                style=ft.ButtonStyle(
                    color=ft.Colors.RED_300,
                    icon_color=ft.Colors.RED_300,
                ),
            )
            if is_active
            else ft.Button(
                content=ft.Text("Connect"),
                icon=ft.Icons.POWER,
                on_click=on_connect,
            )
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if is_active else ft.Icons.CLOUD_OUTLINED,
                        color=ft.Colors.GREEN_400 if is_active else ft.Colors.BLUE_200,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(ctx.name, size=14, weight=ft.FontWeight.W_600),
                            ft.Text(
                                f"{ctx.cluster} · {ctx.user}",
                                size=11,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    action_btn,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=10,
            border_radius=8,
            ink=True,
            on_click=on_tap,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.GREEN) if is_active else None,
        )

    # ── actions ───────────────────────────────────────────────────────

    def _show_detail(self, ctx: KubeContext) -> None:
        self._detail.content = ft.Column(
            controls=[
                ft.Text("Context details", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self._detail_row("Name", ctx.name),
                self._detail_row("Cluster", ctx.cluster),
                self._detail_row("User", ctx.user),
                self._detail_row("Namespace", ctx.namespace or "default"),
            ],
            spacing=8,
        )
        self._page.update()

    @staticmethod
    def _detail_row(label: str, value: str) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Text(f"{label}:", size=12, color=ft.Colors.GREY_500, width=100),
                ft.Text(value, size=13, selectable=True),
            ]
        )

    async def _connect(self, ctx: KubeContext) -> None:
        try:
            api_client = await asyncio.to_thread(
                self._manager.load_context,
                ctx.name,
            )
            from kubeidea.kube.resources import list_namespaces

            namespaces = await asyncio.to_thread(list_namespaces, api_client)

            self._ctx.switch_context(ctx.name, api_client, namespaces)
            self._detail.content = ft.Column(
                controls=[
                    ft.Text("Context details", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self._detail_row("Name", ctx.name),
                    self._detail_row("Cluster", ctx.cluster),
                    self._detail_row("User", ctx.user),
                    self._detail_row("Namespace", ctx.namespace or "default"),
                    ft.Divider(),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=18),
                            ft.Text("Connected", size=13, color=ft.Colors.GREEN_400),
                        ],
                        spacing=6,
                    ),
                    ft.Text(
                        f"{len(namespaces)} namespace(s) accessible",
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                spacing=8,
            )
            # refresh tile list to show active indicator
            self._load_contexts()
            if self._on_connected:
                result = self._on_connected()
                if asyncio.iscoroutine(result):
                    await result

        except Exception as exc:
            self._detail.content = ft.Column(
                controls=[
                    ft.Text("Connection failed", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400),
                    ft.Divider(),
                    self._detail_row("Context", ctx.name),
                    self._detail_row("Cluster", ctx.cluster),
                    ft.Divider(),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400, size=18),
                            ft.Text(str(exc), size=12, color=ft.Colors.RED_300, selectable=True),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=8,
            )
            self._page.update()

    async def _disconnect(self) -> None:
        """Disconnect from the active cluster."""
        ctx_name = self._ctx.current_context or "cluster"
        self._ctx.disconnect()

        self._detail.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CLOUD_OFF, color=ft.Colors.GREY_500, size=18),
                        ft.Text("Disconnected", size=13, color=ft.Colors.GREY_500),
                    ],
                    spacing=6,
                ),
                ft.Text(
                    f"Disconnected from {ctx_name}",
                    size=12,
                    color=ft.Colors.GREY_500,
                ),
            ],
            spacing=8,
        )
        self._load_contexts()
        if self._on_disconnected:
            result = self._on_disconnected()
            if asyncio.iscoroutine(result):
                await result

    def _on_refresh(self, _e: Any) -> None:
        self._load_contexts()
