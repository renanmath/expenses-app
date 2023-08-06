import flet as ft


class Aplication:
    def __init__(self) -> None:
        self.page: ft.Page = None

    def main(self, page: ft.Page):
        self.page = page
        self.run()

    def minus_click(self):
        self.txt_number.value = str(int(self.txt_number.value) - 1)
        self.page.update()

    def run(self):
        self.page.title = 'Flet counter example'

        self.txt_number = ft.TextField(
            value='0', text_align=ft.TextAlign.RIGHT, width=100
        )

        self.page.add(
            ft.Row(
                [
                    ft.IconButton(
                        ft.icons.REMOVE, on_click=lambda _: self.minus_click()
                    ),
                    self.txt_number,
                    ft.IconButton(ft.icons.ADD),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )


def main(page: ft.Page):
    app = Aplication()
    app.main(page=page)


if __name__ == '__main__':
    ft.app(target=main)
