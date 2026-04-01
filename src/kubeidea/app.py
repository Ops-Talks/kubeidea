"""Main application entry point for Kube-IDEA."""

import flet as ft

from kubeidea.ui.navigation import build_navigation
from kubeidea.ui.theme import apply_theme
from kubeidea.ui.views.home import HomeView
from kubeidea.ui.views.placeholder import PlaceholderView


def main(page: ft.Page) -> None:
    """Bootstrap the Kube-IDEA desktop application."""
    page.title = "Kube-IDEA"
    page.window.width = 1200
    page.window.height = 800

    apply_theme(page)

    views: list[ft.Control] = [
        HomeView(page),
        PlaceholderView("Clusters", ft.Icons.CLOUD),
        PlaceholderView("Logs", ft.Icons.TERMINAL),
        PlaceholderView("Metrics", ft.Icons.MONITOR_HEART),
        PlaceholderView("YAML Editor", ft.Icons.CODE),
        PlaceholderView("RBAC Inspector", ft.Icons.SECURITY),
        PlaceholderView("Plugins", ft.Icons.EXTENSION),
        PlaceholderView("Settings", ft.Icons.SETTINGS),
    ]

    content_area = ft.Column(controls=[views[0]], expand=True)

    def on_nav_change(index: int) -> None:
        content_area.controls.clear()
        content_area.controls.append(views[index])
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
