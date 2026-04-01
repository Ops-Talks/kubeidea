"""Main application entry point for Kube-IDEA."""

import flet as ft

from kubeidea.config.settings import AppSettings
from kubeidea.core.context import AppContext
from kubeidea.ui.navigation import build_navigation
from kubeidea.ui.theme import apply_theme
from kubeidea.ui.views.clusters import ClustersView
from kubeidea.ui.views.explorer import ExplorerView
from kubeidea.ui.views.home import HomeView
from kubeidea.ui.views.placeholder import PlaceholderView
from kubeidea.ui.views.settings import SettingsView


async def main(page: ft.Page) -> None:
    """Bootstrap the Kube-IDEA desktop application."""
    page.title = "Kube-IDEA"
    page.window.width = 1200
    page.window.height = 800

    settings = AppSettings.load()
    apply_theme(page, dark=settings.theme_dark)

    app_ctx = AppContext()

    explorer_view = ExplorerView(page, app_ctx)

    async def _on_cluster_connected() -> None:
        await explorer_view.refresh()

    async def _on_cluster_disconnected() -> None:
        await explorer_view.refresh()

    clusters_view = ClustersView(
        page, app_ctx,
        on_connected=_on_cluster_connected,
        on_disconnected=_on_cluster_disconnected,
    )

    views: list[ft.Control] = [
        HomeView(page),
        clusters_view,
        explorer_view,
        PlaceholderView("Logs", ft.Icons.TERMINAL),
        PlaceholderView("Metrics", ft.Icons.MONITOR_HEART),
        PlaceholderView("YAML Editor", ft.Icons.CODE),
        PlaceholderView("RBAC Inspector", ft.Icons.SECURITY),
        PlaceholderView("Plugins", ft.Icons.EXTENSION),
        SettingsView(page),
    ]

    content_area = ft.Column(controls=[views[0]], expand=True)

    async def on_nav_change(index: int) -> None:
        content_area.controls.clear()
        content_area.controls.append(views[index])
        # auto-refresh explorer when navigating to it
        if isinstance(views[index], ExplorerView):
            await explorer_view.refresh()
        page.update()

    navigation = build_navigation(page, on_nav_change)

    page.add(
        ft.Row(
            controls=[navigation, content_area],
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main)
