"""Home view — landing page for Kube-IDEA."""

import flet as ft


class HomeView(ft.Column):
    """Main home view shown when the application starts."""

    def __init__(self, page: ft.Page) -> None:
        super().__init__(
            expand=True,
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Welcome to Kube-IDEA", size=28, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "Kubernetes desktop IDE — explore clusters, stream logs, "
                                "run exec, manage port-forwards, and more.",
                                size=14,
                            ),
                            ft.Divider(),
                            ft.Text("Select a section from the navigation rail to get started.", size=12),
                        ],
                        spacing=10,
                    ),
                    padding=30,
                    expand=True,
                ),
            ],
        )
        self._page = page
