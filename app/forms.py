from models import Users
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError, Field
from wtforms.validators import InputRequired, Length
from datetime import datetime
import secrets
from typing import List, Optional, Dict, NoReturn, Any
from collections.abc import Sequence


class signup_form(FlaskForm):
    username = StringField('Логин:', validators=[InputRequired(), Length(1, 80)], render_kw={"class": "form-control", "placeholder": "Логин..."})
    name = StringField('Имя:', validators=[Length(0, 80)], render_kw={"class": "form-control", "placeholder": "Имя..."})
    surname = StringField('Фамилия:', validators=[Length(0, 80)], render_kw={"class": "form-control", "placeholder": "Фамилия..."})
    patronymic = StringField('Отчество:', validators=[Length(0, 80)], render_kw={"class": "form-control", "placeholder": "Отчество..."})
    password = PasswordField('Пароль:', validators=[InputRequired(), Length(8, 80)], render_kw={"class": "form-control", "placeholder": "Пароль..."})
    repeat_password = PasswordField('Повторите пароль:', validators=[InputRequired(), Length(8, 80)], render_kw={"class": "form-control", "placeholder": "Повторите пароль..."})
    plan_edit_permission = BooleanField('Разрешение на редактирование плановых значений', render_kw={'class': 'form-check-input'})
    fact_edit_permission = BooleanField('Разрешение на редактирование фактических значений', render_kw={'class': 'form-check-input'})
    all_months_edit_permission = BooleanField('Разрешение на редактирование значений всех месяцев', render_kw={'class': 'form-check-input'})
    facility_ULRZ = BooleanField('УЛРЗ', render_kw={'class': 'form-check-input'})
    facility_UULVRZ = BooleanField('УУЛВРЗ', render_kw={'class': 'form-check-input'})
    facility_OLRZ = BooleanField('ОЛРЗ', render_kw={'class': 'form-check-input'})
    facility_CHERZ = BooleanField('ЧЭРЗ', render_kw={'class': 'form-check-input'})
    facility_ATRZ = BooleanField('АТРЗ', render_kw={'class': 'form-check-input'})
    facility_RERZ = BooleanField('РЭРЗ', render_kw={'class': 'form-check-input'})
    facility_VTRZ = BooleanField('ВТРЗ', render_kw={'class': 'form-check-input'})
    facility_YAERZ = BooleanField('ЯЭРЗ', render_kw={'class': 'form-check-input'})
    facility_AU = BooleanField('АУ', render_kw={'class': 'form-check-input'})
    submit = SubmitField('Создать пользователя', render_kw={'class': 'btn btn-primary'})
    
    def validate_username(self, username: Field):
        if Users.query.filter_by(username=username.data).first():
            raise ValidationError('Такой логин уже существует.')
    
    def validate_password(self, password: Field) -> bool:
        if password.data != self.repeat_password.data:
            raise ValidationError('Пароли не совпадают.')


class signin_form(FlaskForm):
    username = StringField('Логин:', validators=[InputRequired(message='Введите логин.')], render_kw={"class": "form-control", "placeholder": "Логин..."})
    password = PasswordField('Пароль:', validators=[InputRequired(message='Введите пароль.')], render_kw={"class": "form-control", "placeholder": "Пароль..."})
    submit = SubmitField('Войти', render_kw={"class": "btn btn-primary"})


class profile_edit_form(FlaskForm):
    name = StringField('Имя:', validators=[Length(0, 80)], render_kw={"class": "form-control", "placeholder": "Имя..."})
    surname = StringField('Фамилия:', validators=[Length(0, 80)], render_kw={"class": "form-control", "placeholder": "Фамилия..."})
    patronymic = StringField('Отчество:', validators=[Length(0, 80)], render_kw={"class": "form-control", "placeholder": "Отчество..."})
    plan_edit_permission = BooleanField('Разрешение на редактирование плановых значений', render_kw={'class': 'form-check-input'})
    fact_edit_permission = BooleanField('Разрешение на редактирование фактических значений', render_kw={'class': 'form-check-input'})
    all_months_edit_permission = BooleanField('Разрешение на редактирование значений всех месяцев', render_kw={'class': 'form-check-input'})
    facility_ULRZ = BooleanField('УЛРЗ', render_kw={'class': 'form-check-input'})
    facility_UULVRZ = BooleanField('УУЛВРЗ', render_kw={'class': 'form-check-input'})
    facility_OLRZ = BooleanField('ОЛРЗ', render_kw={'class': 'form-check-input'})
    facility_CHERZ = BooleanField('ЧЭРЗ', render_kw={'class': 'form-check-input'})
    facility_ATRZ = BooleanField('АТРЗ', render_kw={'class': 'form-check-input'})
    facility_RERZ = BooleanField('РЭРЗ', render_kw={'class': 'form-check-input'})
    facility_VTRZ = BooleanField('ВТРЗ', render_kw={'class': 'form-check-input'})
    facility_YAERZ = BooleanField('ЯЭРЗ', render_kw={'class': 'form-check-input'})
    facility_AU = BooleanField('АУ', render_kw={'class': 'form-check-input'})
    submit = SubmitField('Сохранить', render_kw={'class': 'btn btn-primary'})


class change_password_form(FlaskForm):
    old_password = PasswordField('Старый пароль:', render_kw={"class": "form-control", "placeholder": "Старый пароль..."})
    new_password = PasswordField('Новый пароль:', validators=[InputRequired(message='Введите пароль.'), Length(8, 80)], render_kw={"class": "form-control", "placeholder": "Новый пароль..."})
    repeat_new_password = PasswordField('Новый пароль:', validators=[InputRequired(message='Введите пароль.'), Length(8, 80)], render_kw={"class": "form-control", "placeholder": "Повторите новый пароль..."})
    submit = SubmitField('Изменить пароль', render_kw={'class': 'btn btn-primary'})

    def validate_new_password(self, new_password: Field) -> bool:
        if new_password.data != self.repeat_new_password.data:
            raise ValidationError('Пароли не совпадают.')

class TableForm:
    def __init__(self,
                 data: List,
                 fields: Dict[str, str],
                 main_column: str,
                 fact_edit_permission: bool = False,
                 plan_edit_permission: bool = False,
                 all_months_edit_permission: bool = False,
                 field_step: float | int = 1,
                 field_validation_min_value: Optional[float | int] = None,
                 field_validation_max_value: Optional[float | int] = None,
                 **kwargs) -> str:
        self.form: Dict[Dict[str, List[str]]] | Dict[Dict[str, Dict[str, List[str]]]] = {}
        self.field_ids: Dict[str, Any] = {}
        self.data = data
        self.fields = fields
        self.main_column = main_column
        self.fact_edit_permission = fact_edit_permission
        self.plan_edit_permission = plan_edit_permission
        self.all_month_edit_permission = all_months_edit_permission
        self.field_step = field_step
        self.field_validation_min_value = field_validation_min_value
        self.field_validation_max_value = field_validation_max_value
        self.current_month = int(kwargs.get('current_month', datetime.now().month))
        self.field_style = kwargs.get('field_style', 'width: 100%;')
        self.csrf_token = secrets.token_hex(16)

    def _generate(self) -> None | NoReturn:
        self.form: Dict[Dict[str, List[str]]] = {}
        self.field_ids: Dict[str, Any] = {}
        for row in self.data:
            section: str = getattr(row, self.main_column).name
            if section not in self.form:
                self.form[section] = {i: [None]*12 for i in self.fields.keys()}
            for key, value_type in self.fields.items():
                value = getattr(row, key)
                if value is None:
                    value = ""
                name = f"{key}_{row.id}"
                if ((value_type == 'fact' and self.fact_edit_permission
                     ) or (value_type == 'plan' and self.plan_edit_permission)
                     ) and (self.all_month_edit_permission or self.current_month == row.month.month):
                    self.field_ids[name] = value
                    field = f'''
<input type="number" style="{self.field_style}" name="{name}" id="{name}" step="{self.field_step}"
min="{self.field_validation_min_value}" max="{self.field_validation_max_value}" value="{value}">
'''.replace('\n', ' ')
                else:
                    field = f'''
<p style="{self.field_style}" id="{self.name}">{value}</p>
'''.replace('\n', ' ')
                self.form[section][key][row.month.month-1] = field
    
    def _generate_with_levels(self, additional_level_range: Sequence, level_column_name: str) -> None | NoReturn:
        self.form: Dict[Dict[str, Dict[str, List[str]]]]
        self.field_ids: Dict[str, Any] = {}
        for row in self.data:
            section: str = getattr(row, self.main_column).name
            if section not in self.form:
                self.form[section] = {level: {i: [None]*12 for i in self.fields.keys()} for level in additional_level_range}
            for key, value_type in self.fields.items():
                value = getattr(row, key)
                if value is None:
                    value = ""
                name = f"{key}_{row.id}"
                if ((value_type == 'fact' and self.fact_edit_permission
                     ) or (value_type == 'plan' and self.plan_edit_permission)
                     ) and (self.all_month_edit_permission or self.current_month == row.month.month):
                    self.field_ids[name] = value
                    field = f'''
<input type="number" style="{self.field_style}" name="{name}" id="{name}" step="{self.field_step}"
min="{self.field_validation_min_value}" max="{self.field_validation_max_value}" value="{value}">
'''.replace('\n', ' ')
                else:
                    field = f'''
<p style="{self.field_style}" id="{self.name}">{value}</p>
'''.replace('\n', ' ')
                self.form[section][getattr(row, level_column_name)][key][row.month.month-1] = field

    def generate(self, additional_level_range: Optional[Sequence] = None,
                 level_column_name: Optional[str] = None, sort: bool = True) -> None | NoReturn:
        if additional_level_range is None:
            self._generate()
        else:
            self._generate_with_levels(additional_level_range, level_column_name)
        if sort:
            self.form = dict(sorted(self.form.items()))
    
    def validate(self, csrf_token: str, form_data: Dict[str, Any]) -> Dict[str, Any] | NoReturn:
        changed_data: Dict[str, Any] = {}
        if not self.csrf_token == csrf_token:
            raise ConnectionError('Wrong csrf token.')
        for field_name, field_data in form_data.items():
            value = self.field_ids.get(field_name)
            if value is None:
                raise ConnectionRefusedError(f'{field_name} is not allowed to change for current user or not exists.')
            if field_data != '' and field_data is not None:
                if ((self.field_validation_min_value is not None
                     ) and (float(field_data) < self.field_validation_min_value)
                     ) or ((self.field_validation_max_value is not None
                            ) and (float(field_data) > self.field_validation_max_value)):
                    raise ValueError(f'Value (with id {field_name}) is out of bound ({self.field_validation_min_value} and {self.field_validation_max_value})')
            if value != field_data:
                changed_data[field_name] = field_data
        return changed_data