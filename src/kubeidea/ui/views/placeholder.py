"""Generic placeholder view for sections not yet implemented."""

import flet as ft


class PlaceholderView(ft.Column):
    """Temporary placeholder shown for features under development."""

    def __init__(self, section: str, icon: ft.IconData) -> None:
        super().__init__(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=64, color=ft.Colors.BLUE_200),
                ft.Text(section, size=22, weight=ft.FontWeight.BOLD),
                ft.Text("This section is under development.", size=13, color=ft.Colors.GREY_500),
            ],
        )
