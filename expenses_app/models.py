from typing import Any
import flet as ft
from expenses_app.constants import (
    MAIN_PURPLE,
    MAIN_GREEN,
    MAIN_BLUE,
    LIGHT_GREEN,
    DEEP_PURPLE,
)


class MyDivider(ft.Divider):
    def __init__(self):
        super().__init__(height=2, color=MAIN_PURPLE)


class MyButton(ft.ElevatedButton):
    def __init__(self, text: str, on_click: Any, **kwargs):
        super().__init__(
            text=text,
            on_click=on_click,
            bgcolor=LIGHT_GREEN,
            color=MAIN_PURPLE,
            **kwargs
        )


class MyText(ft.Text):
    def __init__(self, value: str, **kwargs):
        super().__init__(
            value=value,
            text_align=ft.TextAlign.CENTER,
            weight='bold',
            color=DEEP_PURPLE,
            **kwargs
        )
