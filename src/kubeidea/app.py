"""Main application entry point for Kube-IDEA."""

import flet as ft

from kubeidea.ui.navigation import build_navigation
from kubeidea.ui.theme import apply_theme
from kubeidea.ui.views.home import HomeView


def main(page: ft.Page) -> None:
    """Bootstrap the Kube-IDEA desktop application."""
    page.title = "Kube-IDEA"
    page.window.width = 1200
    page.window.height = 800

    apply_theme(page)

    navigation = build_navigation(page)
    home_view = HomeView(page)

    page.add(
        ft.Row(
            controls=[navigation, home_view],
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
