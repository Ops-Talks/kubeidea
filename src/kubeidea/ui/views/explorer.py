"""Explorer view — browse Kubernetes resources with categorised tabs.

Layout
------
Header  : Title · connection chip · namespace dropdown · search · refresh
Body    : ft.Row
          ├── Left  (expand=2)  — 5 category tabs, each a ListView of rows
          └── Right (expand=3)  — detail panel (info / events / YAML / actions)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import flet as ft

from kubeidea.core.context import AppContext
from kubeidea.kube.resources import (
    list_configmaps,
    list_cronjobs,
    list_daemonsets,
    list_deployments,
    list_events,
    list_hpa,
    list_ingresses,
    list_jobs,
    list_networkpolicies,
    list_nodes,
    list_persistentvolumeclaims,
    list_persistentvolumes,
    list_pods,
    list_secrets,
    list_serviceaccounts,
    list_services,
    list_statefulsets,
)
from kubeidea.ui.views._explorer_detail import DetailPanel
from kubeidea.ui.views._explorer_rows import (
    CATEGORIES,
    build_resource_row,
    build_section_header,
)

logger = logging.getLogger(__name__)

# ── Loader registry (kind → callable) ────────────────────────────
_LOADERS: dict[str, Any] = {
    "Pod": list_pods,
    "Deployment": list_deployments,
    "StatefulSet": list_statefulsets,
    "DaemonSet": list_daemonsets,
    "Job": list_jobs,
    "CronJob": list_cronjobs,
    "Service": list_services,
    "Ingress": list_ingresses,
    "NetworkPolicy": list_networkpolicies,
    "ConfigMap": list_configmaps,
    "Secret": list_secrets,
    "ServiceAccount": list_serviceaccounts,
    "PersistentVolume": list_persistentvolumes,
    "PersistentVolumeClaim": list_persistentvolumeclaims,
    "Node": list_nodes,
    "HorizontalPodAutoscaler": list_hpa,
    "Event": list_events,
}

# Resources whose loader does NOT accept a namespace argument
_CLUSTER_SCOPED: set[str] = {"Node", "PersistentVolume"}


def _parse_label_selector(selector: str) -> dict[str, str]:
    """Parse a comma-separated label selector into key-value pairs."""
    result: dict[str, str] = {}
    for part in selector.split(","):
        part = part.strip()
        if "=" in part:
            key, _, value = part.partition("=")
            result[key.strip()] = value.strip()
    return result


def _filter_by_labels(items: list[Any], selector: str) -> list[Any]:
    """Filter resources matching ALL labels in the selector."""
    required = _parse_label_selector(selector)
    if not required:
        return items
    return [r for r in items if all(getattr(r, "labels", {}).get(k) == v for k, v in required.items())]


def _sort_resources(
    items: list[Any],
    field: str,
    ascending: bool,
) -> list[Any]:
    """Sort resources by the given field."""
    if not items:
        return items

    def _name_key(r: Any) -> str:
        return getattr(r, "name", getattr(r, "reason", "")).lower()

    def _age_key(r: Any) -> str:
        return getattr(r, "age", "")

    key_fn = _name_key if field == "name" else _age_key
    return sorted(items, key=key_fn, reverse=not ascending)


class ExplorerView(ft.Column):
    """Full-featured Kubernetes resource explorer with search and detail."""

    def __init__(self, page: ft.Page, ctx: AppContext) -> None:
        super().__init__(expand=True, spacing=0)
        self._page = page
        self._ctx = ctx

        # cached data: kind → list[Model]
        self._data: dict[str, list[Any]] = {}
        self._search_text: str = ""
        self._label_filter: str = ""
        self._status_filter: str = ""
        self._sort_field: str = "name"  # "name" or "age"
        self._sort_ascending: bool = True

        # ── header controls ───────────────────────────────────────
        self._connection_chip = ft.Chip(
            label=ft.Text("Not connected"),
            leading=ft.Icon(ft.Icons.CLOUD_OFF, size=16),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.RED),
        )

        self._ns_dropdown = ft.Dropdown(
            label="Namespace",
            width=220,
            on_select=self._on_namespace_change,
        )

        self._search_field = ft.TextField(
            label="Filter by name",
            prefix_icon=ft.Icons.SEARCH,
            width=250,
            height=40,
            text_size=13,
            on_change=self._on_search_change,
        )

        self._label_field = ft.TextField(
            label="Filter by labels",
            prefix_icon=ft.Icons.LABEL,
            width=220,
            height=40,
            text_size=13,
            hint_text="app=nginx,tier=web",
            on_change=self._on_label_change,
        )

        self._status_dropdown = ft.Dropdown(
            label="Status",
            width=150,
            height=40,
            options=[
                ft.DropdownOption(key="", text="All"),
                ft.DropdownOption(key="Running", text="Running"),
                ft.DropdownOption(key="Pending", text="Pending"),
                ft.DropdownOption(key="Failed", text="Failed"),
                ft.DropdownOption(key="Succeeded", text="Succeeded"),
                ft.DropdownOption(key="Ready", text="Ready"),
                ft.DropdownOption(key="NotReady", text="NotReady"),
                ft.DropdownOption(key="Bound", text="Bound"),
                ft.DropdownOption(key="Available", text="Available"),
                ft.DropdownOption(key="Complete", text="Complete"),
            ],
            on_select=self._on_status_change,
        )

        self._sort_button = ft.IconButton(
            ft.Icons.SORT_BY_ALPHA,
            tooltip="Sort by name (ascending)",
            on_click=self._on_sort_toggle,
        )

        self._refresh_btn = ft.IconButton(
            ft.Icons.REFRESH,
            tooltip="Refresh resources",
            on_click=self._on_refresh,
        )

        # ── one ListView per category tab ─────────────────────────
        self._category_lists: list[ft.ListView] = [
            ft.ListView(expand=True, spacing=2, padding=8)
            for _ in CATEGORIES
        ]

        # Cast for TabBarView which expects list[Control] (list is invariant)
        _tab_views: list[ft.Control] = [*self._category_lists]

        # ── category tabs (Tabs ▸ TabBar + TabBarView) ────────────
        self._tabs = ft.Tabs(
            length=len(CATEGORIES),
            selected_index=0,
            expand=True,
            on_change=self._on_tab_change,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[ft.Tab(label=cat[0], icon=cat[1]) for cat in CATEGORIES],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=_tab_views,
                    ),
                ],
            ),
        )

        # ── detail panel (right side) ─────────────────────────────
        self._detail_panel = DetailPanel(
            page=page,
            ctx=ctx,
            on_close=self._on_detail_close,
            on_resource_deleted=self._on_resource_mutated,
        )

        # ── assemble layout ───────────────────────────────────────
        self.controls = [
            # row 1 — title + connection chip
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            "Explorer",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                        self._connection_chip,
                    ],
                    spacing=12,
                ),
                padding=ft.Padding.only(left=24, right=24, top=16),
            ),
            # row 2 — namespace dropdown, search, refresh
            ft.Container(
                content=ft.Row(
                    controls=[
                        self._ns_dropdown,
                        self._search_field,
                        self._label_field,
                        self._status_dropdown,
                        self._sort_button,
                        self._refresh_btn,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=ft.Padding.only(
                    left=24,
                    right=24,
                    top=8,
                    bottom=4,
                ),
            ),
            ft.Divider(height=1),
            # body — split: tabs | detail
            ft.Row(
                controls=[
                    ft.Container(content=self._tabs, expand=2),
                    ft.VerticalDivider(width=1),
                    ft.Container(
                        content=self._detail_panel,
                        expand=3,
                    ),
                ],
                expand=True,
                spacing=0,
            ),
        ]

    # ── public API (called by app.py) ─────────────────────────────

    async def refresh(self) -> None:
        """Reload namespace list and all resources."""
        if not self._ctx.connected:
            self._show_not_connected()
            return

        self._connection_chip.label = ft.Text(
            self._ctx.current_context or "",
        )
        self._connection_chip.leading = ft.Icon(
            ft.Icons.CLOUD_DONE,
            size=16,
        )
        self._connection_chip.bgcolor = ft.Colors.with_opacity(
            0.1,
            ft.Colors.GREEN,
        )

        self._ns_dropdown.options = [ft.DropdownOption(key=ns) for ns in self._ctx.namespaces]
        self._ns_dropdown.value = self._ctx.current_namespace

        await asyncio.to_thread(self._load_all_resources)
        self._render_all_categories()
        self._page.update()

    # ── data loading ──────────────────────────────────────────────

    def _load_all_resources(self) -> None:
        """Fetch every resource kind from the cluster."""
        client = self._ctx.api_client
        if not client:
            return
        ns = self._ctx.current_namespace
        for kind, loader in _LOADERS.items():
            try:
                if kind in _CLUSTER_SCOPED:
                    self._data[kind] = loader(client)
                else:
                    self._data[kind] = loader(client, ns)
            except Exception as exc:
                logger.warning("Failed to load %s: %s", kind, exc)
                self._data[kind] = []

    # ── rendering ─────────────────────────────────────────────────

    def _render_all_categories(self) -> None:
        for idx, (_, _, kinds) in enumerate(CATEGORIES):
            self._render_category(idx, kinds)

    def _render_category(
        self,
        cat_idx: int,
        kinds: list[str],
    ) -> None:
        lv = self._category_lists[cat_idx]
        lv.controls.clear()
        search = self._search_text.lower()
        label_filter = self._label_filter.strip()
        status_filter = self._status_filter
        any_visible = False

        for kind in kinds:
            items = self._data.get(kind, [])

            # Name filter
            if search:
                items = [
                    r
                    for r in items
                    if search
                    in getattr(
                        r,
                        "name",
                        getattr(r, "reason", ""),
                    ).lower()
                ]

            # Label filter (format: "key=value,key2=value2")
            if label_filter:
                items = _filter_by_labels(items, label_filter)

            # Status filter
            if status_filter:
                items = [r for r in items if getattr(r, "status", "") == status_filter]

            # Sorting
            items = _sort_resources(
                items,
                self._sort_field,
                self._sort_ascending,
            )

            if not items:
                continue
            any_visible = True
            lv.controls.append(build_section_header(kind, len(items)))
            for resource in items:
                lv.controls.append(
                    build_resource_row(
                        kind,
                        resource,
                        self._on_resource_selected,
                    ),
                )

        if not any_visible:
            has_filter = search or label_filter or status_filter
            msg = "No matching resources." if has_filter else "No resources found."
            lv.controls.append(
                ft.Container(
                    content=ft.Text(
                        msg,
                        size=13,
                        color=ft.Colors.GREY_500,
                    ),
                    padding=20,
                    alignment=ft.Alignment(0, 0),
                ),
            )

    # ── disconnected state ────────────────────────────────────────

    def _show_not_connected(self) -> None:
        self._connection_chip.label = ft.Text("Not connected")
        self._connection_chip.leading = ft.Icon(
            ft.Icons.CLOUD_OFF,
            size=16,
        )
        self._connection_chip.bgcolor = ft.Colors.with_opacity(
            0.1,
            ft.Colors.RED,
        )
        self._ns_dropdown.options = []
        self._ns_dropdown.value = None
        self._data.clear()

        for lv in self._category_lists:
            lv.controls.clear()
            lv.controls.append(self._disconnected_placeholder())

        self._detail_panel.hide()
        self._page.update()

    @staticmethod
    def _disconnected_placeholder() -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.CLOUD_OFF,
                        size=40,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        "Connect to a cluster first.",
                        size=14,
                        color=ft.Colors.GREY_500,
                    ),
                    ft.Text(
                        "Go to Clusters and press Connect.",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment(0, 0),
            padding=40,
        )

    # ── callbacks ─────────────────────────────────────────────────

    async def _on_namespace_change(self, _e: Any) -> None:
        if self._ns_dropdown.value:
            self._ctx.switch_namespace(self._ns_dropdown.value)
            await asyncio.to_thread(self._load_all_resources)
            self._render_all_categories()
            self._detail_panel.hide()
            self._page.update()

    async def _on_refresh(self, _e: Any) -> None:
        await self.refresh()

    def _on_tab_change(self, _e: Any) -> None:
        pass  # TabBarView handles visibility automatically

    def _on_search_change(self, _e: Any) -> None:
        self._search_text = self._search_field.value or ""
        self._render_all_categories()
        self._page.update()

    def _on_label_change(self, _e: Any) -> None:
        self._label_filter = self._label_field.value or ""
        self._render_all_categories()
        self._page.update()

    def _on_status_change(self, _e: Any) -> None:
        self._status_filter = self._status_dropdown.value or ""
        self._render_all_categories()
        self._page.update()

    def _on_sort_toggle(self, _e: Any) -> None:
        if self._sort_field == "name" and self._sort_ascending:
            self._sort_ascending = False
            self._sort_button.tooltip = "Sort by name (descending)"
            self._sort_button.icon = ft.Icons.SORT_BY_ALPHA
        elif self._sort_field == "name" and not self._sort_ascending:
            self._sort_field = "age"
            self._sort_ascending = True
            self._sort_button.tooltip = "Sort by age (ascending)"
            self._sort_button.icon = ft.Icons.ACCESS_TIME
        elif self._sort_field == "age" and self._sort_ascending:
            self._sort_ascending = False
            self._sort_button.tooltip = "Sort by age (descending)"
            self._sort_button.icon = ft.Icons.ACCESS_TIME
        else:
            self._sort_field = "name"
            self._sort_ascending = True
            self._sort_button.tooltip = "Sort by name (ascending)"
            self._sort_button.icon = ft.Icons.SORT_BY_ALPHA
        self._render_all_categories()
        self._page.update()

    def _on_resource_selected(self, kind: str, resource: Any) -> None:
        self._detail_panel.show(kind, resource)
        self._page.update()

    def _on_detail_close(self) -> None:
        self._detail_panel.hide()
        self._page.update()

    async def _on_resource_mutated(self) -> None:
        """Refresh lists after a delete / scale / restart."""
        await asyncio.to_thread(self._load_all_resources)
        self._render_all_categories()
        self._page.update()
