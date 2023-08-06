import flet as ft
import json
import csv
from copy import copy, deepcopy
import pendulum
from expenses_opt.models.expense import (
    Expense,
    ExpenseRange,
    build_expenses_from_csv,
)
from expenses_opt.models.portfolio import Budget, Portfolio
from expenses_opt.optimization.optimizer import (
    Optimizer,
    OptmizationParameters,
)
from expenses_opt.exceptions import (
    InfeasibleProblemException,
    InvalidDataException,
)
from expenses_opt.constants import Priority
from expenses_app.models import MyButton, MyDivider, MyText


def str_2_float(value: str):
    return round(float(value.strip().replace('.', '').replace(',', '.')), 2)


def date_2_string(date: pendulum.Date):
    return f'{date.day}/{date.month}/{date.year}'


class Aplication:
    def __init__(self) -> None:
        self.page: ft.Page = None
        self.expenses_data: list[Expense] = list()
        self.file_picker = ft.FilePicker(on_result=self.handle_import)
        self.file_export = ft.FilePicker(on_result=self.handle_export)

        self.title_text = MyText(value='Otimizador de Gastos Futuros', size=30)

        self.build_expenses_controls()
        self.build_budget_controls()
        self.build_optimization_controls()

        self.opt_button = MyButton(
            text='Otimizar', on_click=lambda _: self.call_optimization()
        )

    def build_optimization_controls(self):
        self.input_opt_target_choice = ft.Dropdown(
            label='Se aproximar do preço',
            options=[
                ft.dropdown.Option('Desejável'),
                ft.dropdown.Option('Mínimo'),
                ft.dropdown.Option('Máximo'),
            ],
            border_color=ft.colors.GREEN_600,
            value='Desejável',
        )
        self.input_opt_exponent = ft.TextField(
            label='Expoente de prioridade',
            border_color=ft.colors.GREEN_600,
            hint_text='Valor real maior ou igual a 2',
            value='2',
        )
        self.input_opt_weight = ft.TextField(
            label='Peso do desvio', border_color=ft.colors.GREEN_600, value='0'
        )
        self.input_opt_max_time = ft.TextField(
            label='Tempo máximo de simulação (em segundos)',
            border_color=ft.colors.GREEN_600,
            value='10000',
        )
        self.input_opt_start_date = ft.TextField(
            label='Data de início da simulação',
            border_color=ft.colors.GREEN_600,
            hint_text='DD/MM/AAAA',
        )

        self.input_opt_container1 = ft.Row(
            controls=[self.input_opt_target_choice, self.input_opt_exponent]
        )
        self.input_opt_container2 = ft.Row(
            controls=[
                self.input_opt_weight,
                self.input_opt_max_time,
                self.input_opt_start_date,
            ]
        )

    def build_budget_controls(self):
        self.input_budget_initial = ft.TextField(
            label='Orçamento inicial',
            border_color=ft.colors.GREEN_600,
            prefix_text='R$',
        )
        self.input_budget_recorrent = ft.TextField(
            label='Orçamento recorrente',
            border_color=ft.colors.GREEN_600,
            prefix_text='R$',
        )
        self.input_budget_values = ft.Row(
            controls=[self.input_budget_initial, self.input_budget_recorrent]
        )

        self.input_budget_last_recorrence = ft.TextField(
            label='Data da última recorrência',
            border_color=ft.colors.GREEN_600,
            keyboard_type=ft.KeyboardType.DATETIME,
            hint_text='DD/MM/AAAA',
        )
        self.input_budget_recorrence_type = ft.Dropdown(
            label='Defina a recorrência',
            options=[
                ft.dropdown.Option('Mensal'),
                ft.dropdown.Option('Quinzenal'),
                ft.dropdown.Option('Semanal'),
            ],
            border_color=ft.colors.GREEN_600,
            value='Mensal',
        )
        self.input_budget_number_of_iterations = ft.TextField(
            label='Informe o número de períodos',
            border_color=ft.colors.GREEN_600,
        )
        self.input_budget_params = ft.Row(
            controls=[
                self.input_budget_last_recorrence,
                self.input_budget_recorrence_type,
                self.input_budget_number_of_iterations,
            ]
        )

    def build_expenses_controls(self):
        self.input_expense_name = ft.TextField(
            label='Gasto', border_color=ft.colors.GREEN_600
        )
        self.input_expense_due_date = ft.TextField(
            label='Data Limite',
            border_color=ft.colors.GREEN_600,
            keyboard_type=ft.KeyboardType.DATETIME,
            hint_text='DD/MM/AAAA',
        )
        self.input_expense_info = ft.Row(
            controls=[self.input_expense_name, self.input_expense_due_date]
        )

        self.input_expense_min = ft.TextField(
            label='Preço mínimo',
            prefix_text='R$',
            border_color=ft.colors.GREEN_600,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.input_expense_max = ft.TextField(
            label='Preço máximo',
            prefix_text='R$',
            border_color=ft.colors.GREEN_600,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.input_expense_target = ft.TextField(
            label='Preço desejável',
            prefix_text='R$',
            border_color=ft.colors.GREEN_600,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.input_expense_range = ft.Row(
            [
                self.input_expense_min,
                self.input_expense_max,
                self.input_expense_target,
            ]
        )

        self.input_expense_priority = ft.Dropdown(
            label='Defina a prioridade',
            options=[
                ft.dropdown.Option('Alta'),
                ft.dropdown.Option('Média'),
                ft.dropdown.Option('Baixa'),
            ],
            border_color=ft.colors.GREEN_600,
            value='Baixa',
        )
        self.input_expense_mandatory = ft.Checkbox(
            label='Obrigatório', value=False
        )
        self.input_expense_params = ft.Row(
            [
                self.input_expense_due_date,
                self.input_expense_priority,
                self.input_expense_mandatory,
            ]
        )

        self.expenses_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(value='Nome', weight='bold')),
                ft.DataColumn(
                    ft.Text(value='Preço mínimo', weight='bold'), numeric=True
                ),
                ft.DataColumn(
                    ft.Text(value='Preço máximo', weight='bold'), numeric=True
                ),
                ft.DataColumn(
                    ft.Text(value='Preço desejável', weight='bold'),
                    numeric=True,
                ),
                ft.DataColumn(ft.Text(value='Prioridade', weight='bold')),
                ft.DataColumn(ft.Text(value='Obrigatório', weight='bold')),
                ft.DataColumn(ft.Text(value='Data limite', weight='bold')),
            ],
            border=ft.border.all(2, ft.colors.PURPLE_900),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.colors.PURPLE_900),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.GREEN_900),
        )

        self.add_button = MyButton(
            text='Adicionar Gasto', on_click=lambda _: self.add_expense()
        )

        self.import_csv_button = MyButton(
            text='Importar aquivo csv',
            on_click=lambda _: self.import_from_csv(),
            icon=ft.icons.UPLOAD_FILE,
        )

        self.export_csv_button = MyButton(
            text='Exportar para csv',
            on_click=lambda _: self.export_from_csv(),
            icon=ft.icons.IMPORT_EXPORT,
        )

    def __parse_info_to_expense(
        self,
        price_map: dict,
        name: str,
        due_date: pendulum.Date,
        mandatory: bool = False,
        priority: str = 'Baixa',
    ):
        exp_range = ExpenseRange(
            minimum=price_map['min_price']['value'],
            maximum=price_map['max_price']['value'],
            target=price_map['target_price']['value'],
        )

        priority_map = {
            'ALTA': Priority.HIGHT,
            'MÉDIA': Priority.MEDIUM,
            'BAIXA': Priority.LOW,
        }

        expense = Expense(
            description=name,
            due_date=due_date,
            priority=priority_map[priority.upper()],
            mandatory=mandatory,
            range=exp_range,
        )

        return expense

    def __validate_input_date(self, my_input: ft.TextField):
        raw_value = my_input.value
        try:
            due_date = pendulum.from_format(string=raw_value, fmt='DD/MM/YYYY')
            return due_date
        except ValueError:
            my_input.border_color = ft.colors.RED_900
            return None

    def __validate_numeric_fields(
        self, values_map: dict, error_msg: str, is_int: bool = False
    ):
        for info in values_map.values():
            my_input: ft.TextField = info['input']
            try:
                value = str_2_float(my_input.value)
                if is_int:
                    value = int(value)
                info['value'] = value
                my_input.border_color = ft.colors.GREEN_600
            except ValueError:
                my_input.border_color = ft.colors.RED_900
                self.pop_alert(message=error_msg)
                raise ValueError(error_msg)

    def pop_alert(self, message: str):
        dlg = ft.AlertDialog(title=ft.Text(message))
        self.page.add(dlg)
        dlg.open = True
        self.page.update()

    def main(self, page: ft.Page):
        self.page = page
        self.run()

    def add_expense(self):

        price_map = {
            'min_price': {'value': None, 'input': self.input_expense_min},
            'max_price': {'value': None, 'input': self.input_expense_max},
            'target_price': {
                'value': None,
                'input': self.input_expense_target,
            },
        }

        try:
            self.__validate_numeric_fields(
                price_map, 'Campo de preço inválido'
            )
        except ValueError:
            return None

        name = self.input_expense_name.value
        min_price = f"R$ {price_map['min_price']['value']}"
        max_price = f"R$ {price_map['max_price']['value']}"
        target_price = f"R$ {price_map['target_price']['value']}"
        priority = self.input_expense_priority.value
        mandatory = 'Sim' if self.input_expense_mandatory.value else 'Não'
        due_date = self.__validate_input_date(
            my_input=self.input_expense_due_date
        )

        if due_date is None:
            self.pop_alert(message='Data no formato inválido!')
            return None

        new_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(value=name)),
                ft.DataCell(ft.Text(value=min_price)),
                ft.DataCell(ft.Text(value=max_price)),
                ft.DataCell(ft.Text(value=target_price)),
                ft.DataCell(ft.Text(value=priority)),
                ft.DataCell(ft.Text(value=mandatory)),
                ft.DataCell(ft.Text(value=str(due_date))),
            ]
        )
        self.expenses_table.rows.append(new_row)
        self.page.update()

        expense = self.__parse_info_to_expense(
            price_map=price_map,
            name=name,
            due_date=due_date,
            mandatory=self.input_expense_mandatory.value,
            priority=self.input_expense_priority.value,
        )

        self.expenses_data.append(expense)
        self.clear_expenses_fields()

    def clear_expenses_fields(self):
        fields: list[ft.TextField] = [
            self.input_expense_name,
            self.input_expense_due_date,
            self.input_expense_min,
            self.input_expense_max,
            self.input_expense_target,
        ]

        for field in fields:
            field.value = ''

        self.page.update()

    def import_from_csv(self):
        self.file_picker.pick_files(allowed_extensions=['csv'])

    def export_from_csv(self):
        self.file_export.save_file(
            file_name='gastos.csv',
            allowed_extensions=['csv'])

    def handle_import(self, event: ft.FilePickerResultEvent):
        for file in event.files:

            expenses = build_expenses_from_csv(path=file.path)
            self.expenses_data.extend(expenses)
            for expense in expenses:
                self.add_expense_in_table(expense)

        self.page.update()
    
    def handle_export(self, event):
        print(self.file_export.result.path)

    def add_expense_in_table(self, expense: Expense):
        priority_map = {1: 'Alta', 2: 'Média', 3: 'Baixa'}
        priority = priority_map[expense.priority.value]
        mandatory = 'Sim' if expense.mandatory else 'Não'
        new_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(value=expense.description)),
                ft.DataCell(ft.Text(value=f'R$ {expense.range.minimum}')),
                ft.DataCell(ft.Text(value=f'R$ {expense.range.maximum}')),
                ft.DataCell(ft.Text(value=f'R$ {expense.range.target}')),
                ft.DataCell(ft.Text(value=priority)),
                ft.DataCell(ft.Text(value=mandatory)),
                ft.DataCell(ft.Text(value=date_2_string(expense.due_date))),
            ]
        )
        self.expenses_table.rows.append(new_row)

    def call_optimization(self):

        portfolio = self.run_optimization()
        self.show_optimization_results(portfolio=portfolio)

        self.page.update()

    def run_optimization(self):
        start_date = self.__validate_input_date(self.input_opt_start_date)
        if start_date is None:
            self.pop_alert('Data no formato inválido')
            return None

        opt_params = self.get_optimization_parameters()
        portfolio = self.get_portfolio(start_date)

        try:
            optimizer = Optimizer(
                portfolio=portfolio,
                parameters=opt_params,
                start_date=start_date,
            )

            optimizer.solve_optimization_problem()
            self.pop_alert('Otimização finalizada!')
        except InfeasibleProblemException:
            self.pop_alert(
                'Otimização não encontrou solução factível. Por favor, revise os dados.'
            )

        except InvalidDataException:
            self.pop_alert('Dados inconsistentes. Por favor, revise os dados.')
        except Exception as err:
            self.pop_alert(f'Um erro desconhecido aconteceu: {err}')

        return portfolio

    def get_budget(self, start_date: pendulum.Date):
        price_map = {
            'initial': {'value': None, 'input': self.input_budget_initial},
            'recorrent': {'value': None, 'input': self.input_budget_recorrent},
        }

        try:
            self.__validate_numeric_fields(
                price_map, 'Campo de preço inválido'
            )
        except ValueError:
            return None

        budget_last_recorrence_date = self.__validate_input_date(
            self.input_budget_last_recorrence
        )
        if budget_last_recorrence_date is None:
            self.pop_alert(message='Data no formato inválido!')
            return None

        period = budget_last_recorrence_date - start_date
        last_recorrence = period.days

        values_map = {
            'iterations': {
                'value': None,
                'input': self.input_budget_number_of_iterations,
            }
        }

        try:
            self.__validate_numeric_fields(
                values_map, 'Insira um valor inteiro', True
            )
            iterations = values_map['iterations']['value']
        except ValueError:
            return None

        recurrence_map = {'Mensal': 30, 'Quinzenal': 15, 'Semanal': 7}
        recurrence_key = self.input_budget_recorrence_type.value

        return Budget(
            initial=price_map['initial']['value'],
            recorrent=price_map['recorrent']['value'],
            recurrence=recurrence_map[recurrence_key],
            last_recurrence=last_recorrence,
            iterations=iterations,
        )

    def get_optimization_parameters(self):

        values_map = {
            'exponent': {'value': None, 'input': self.input_opt_exponent},
            'max_time': {'value': None, 'input': self.input_opt_max_time},
        }

        try:
            self.__validate_numeric_fields(
                values_map, 'Insira um valor inteiro', True
            )
        except ValueError:
            return None

        exponent = values_map['exponent']['value']
        max_time = values_map['max_time']['value']

        values_map = {
            'weight': {'value': None, 'input': self.input_opt_weight}
        }

        try:
            self.__validate_numeric_fields(
                values_map, 'Insira um valor numérico válido', True
            )
        except ValueError:
            return None

        weight = values_map['weight']['value']

        params = OptmizationParameters(
            priority_exponent=exponent,
            deviation_weight=weight,
            max_time=max_time,
        )

        return params

    def get_portfolio(self, start_date: pendulum.Date) -> Portfolio:
        budget = self.get_budget(start_date)
        portfolio = Portfolio(
            expenses=deepcopy(self.expenses_data), budget=budget
        )

        return portfolio

    def show_optimization_results(self, portfolio: Portfolio):
        columns = [
            ft.DataColumn(ft.Text(value='Nome', weight='bold')),
            ft.DataColumn(ft.Text(value='Total gasto', weight='bold')),
        ]
        period_map = {
            'Mensal': 'Mês',
            'Quinzenal': 'Quinzena',
            'Semanal': 'Semana',
        }
        period_name = period_map[self.input_budget_recorrence_type.value]
        for it in range(portfolio.budget.iterations):
            columns.append(
                ft.DataColumn(
                    ft.Text(value=f'{period_name} {it+1}', weight='bold'),
                    numeric=True,
                )
            )

        self.results_table = ft.DataTable(
            columns=columns,
            border=ft.border.all(2, ft.colors.PURPLE_900),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.colors.PURPLE_900),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.GREEN_900),
        )

        for expense in portfolio.expenses:
            cells = [
                ft.DataCell(ft.Text(value=expense.description)),
                ft.DataCell(
                    ft.Text(value=f'R$ {sum(expense.partial_spends)}')
                ),
            ]
            for value in expense.partial_spends:
                cells.append(ft.DataCell(ft.Text(value=f'R$ {value}')))

            new_row = ft.DataRow(cells=cells)

            self.results_table.rows.append(new_row)

        self.page.add(MyDivider())
        self.page.add(
            ft.Text(
                value='Gastos sugeridos por período',
                text_align=ft.TextAlign.CENTER,
                weight='bold',
                size=20,
                color=ft.colors.DEEP_PURPLE_500,
            )
        )
        self.page.add(self.results_table)

    def run(self):
        self.page.title = 'Otimizador de Gastos'
        self.page.scroll = ft.ScrollMode.HIDDEN

        self.page.add(self.title_text)
        self.page.add(MyDivider())
        self.page.add(
            ft.Text(
                value='Tabela de gastos',
                text_align=ft.TextAlign.CENTER,
                weight='bold',
                size=20,
                color=ft.colors.DEEP_PURPLE_500,
            )
        )

        self.page.add(self.input_expense_name)
        self.page.add(self.input_expense_range)
        self.page.add(self.input_expense_params)
        self.page.add(self.add_button)
        self.page.add(self.import_csv_button)
        self.page.add(self.export_csv_button)
        self.page.add(self.expenses_table)

        self.page.add(MyDivider())
        self.page.add(
            ft.Text(
                value='Dados do orçamento',
                text_align=ft.TextAlign.CENTER,
                weight='bold',
                size=20,
                color=ft.colors.DEEP_PURPLE_500,
            )
        )
        self.page.add(self.input_budget_values)
        self.page.add(self.input_budget_params)

        self.page.add(MyDivider())
        self.page.add(
            ft.Text(
                value='Parâmetros de otimização',
                text_align=ft.TextAlign.CENTER,
                weight='bold',
                size=20,
                color=ft.colors.DEEP_PURPLE_500,
            )
        )
        self.page.add(self.input_opt_container1)
        self.page.add(self.input_opt_container2)
        self.page.add(self.opt_button)

        self.page.add(MyDivider())
        self.page.add(
            ft.Text(
                value='Resultados',
                text_align=ft.TextAlign.CENTER,
                weight='bold',
                size=25,
                color=ft.colors.DEEP_PURPLE_500,
            )
        )

        self.page.overlay.append(self.file_picker)
        self.page.overlay.append(self.file_export)

        self.page.update()


def main(page: ft.Page):
    app = Aplication()
    app.main(page=page)


if __name__ == '__main__':
    ft.app(target=main)
