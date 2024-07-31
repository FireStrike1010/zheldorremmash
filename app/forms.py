from models import Users
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError, FloatField, Field
from wtforms.validators import InputRequired, Length
from datetime import datetime


class signup_form(FlaskForm):
    username = StringField('Логин:', validators=[InputRequired(), Length(1, 80)], render_kw={"class": "form-control", "placeholder": "Логин..."})
    name = StringField('Имя:', validators=[Length(0, 80)], render_kw={"class": "form-control", "placeholder": "Имя..."})
    surname = StringField('Фамилия:', validators=[Length(0, 80)], render_kw={"class": "form-control", "placeholder": "Фамилия..."})
    patronymic = StringField('Отчество:', validators=[Length(0, 80)], render_kw={"class": "form-control", "placeholder": "Отчество..."})
    password = PasswordField('Пароль:', validators=[InputRequired(), Length(8, 80)], render_kw={"class": "form-control", "placeholder": "Пароль..."})
    repeat_password = PasswordField('Повторите пароль:', validators=[InputRequired(), Length(8, 80)], render_kw={"class": "form-control", "placeholder": "Повторите пароль..."})
    plan_edit_permission = BooleanField('Разрешение на редактирование плановых значений', render_kw={'class': 'form-check-input'})
    fact_edit_permission = BooleanField('Разрешение на редектирование фактических значений', render_kw={'class': 'form-check-input'})
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
    fact_edit_permission = BooleanField('Разрешение на редектирование фактических значений', render_kw={'class': 'form-check-input'})
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



def generate_target_indicator(data: list,
                              fact_edit_permission: bool = False,
                              plan_edit_permission: bool = False,
                              all_months_edit_permission: bool = False):
    form = {}
    ids = []
    current_month = datetime.now().month
    for row in data:
        if row.section.name not in form:
            form[row.section.name] = {'target_plan': [None]*12, 'mandatory_plan': [None]*12, 'fact': [None]*12}
        if all_months_edit_permission or current_month == row.month.month:
            if plan_edit_permission:
                target_plan = f'<input type="number" style="width: 100%;" name="target_plan_{row.id}" step="0.01" min="0" {f'value="{row.target_plan}"' if row.target_plan is not None else ""}>'
                ids.append(f'target_plan_{row.id}')
                mandatory_plan = f'<input type="number" style="width: 100%;" name="mandatory_plan_{row.id}" step="0.01" min="0" {f'value="{row.mandatory_plan}"' if row.mandatory_plan is not None else ""}>'
                ids.append(f'mandatory_plan_{row.id}')
            else:
                target_plan = f'<p>{row.target_plan if row.target_plan is not None else ""}</p>'
                mandatory_plan = f'<p>{row.mandatory_plan if row.mandatory_plan is not None else ""}</p>'
            if fact_edit_permission:
                fact = f'<input type="number" style="width: 100%;" name="fact_{row.id}" step="0.01" min="0" {f'value="{row.fact}"' if row.fact is not None else ""}>'
                ids.append(f'fact_{row.id}')
            else:
                fact = f'<p>{row.fact if row.fact is not None else ""}</p>'
        else:
            target_plan = f'<p>{row.target_plan if row.target_plan is not None else ""}</p>'
            mandatory_plan = f'<p>{row.mandatory_plan if row.mandatory_plan is not None else ""}</p>'
            fact = f'<p>{row.fact if row.fact is not None else ""}</p>'
        form[row.section.name]['target_plan'][row.month.month-1] = target_plan
        form[row.section.name]['mandatory_plan'][row.month.month-1] = mandatory_plan
        form[row.section.name]['fact'][row.month.month-1] = fact
    return form, ids

def generate_action_plan_implementation(data: list,
                              fact_edit_permission: bool = False,
                              plan_edit_permission: bool = False,
                              all_months_edit_permission: bool = False,
                              dk_levels: int = 5):
    form = {}
    ids = []
    current_month = datetime.now().month
    for row in data:
        if row.section.name not in form:
            form[row.section.name] = {i: {'plan': [None]*12, 'fact': [None]*12} for i in range(1, dk_levels+1)}
        if all_months_edit_permission or current_month == row.month.month:
            if plan_edit_permission:
                plan = f'<input type="number" style="width: 100%;" name="plan_{row.id}" step="1" min="0" {f'value="{row.plan}"' if row.plan is not None else ""}>'
                ids.append(f'plan_{row.id}')
            else:
                plan = f'<p>{row.plan if row.plan is not None else ""}</p>'
            if fact_edit_permission:
                fact = f'<input type="number" style="width: 100%;" name="fact_{row.id}" step="1" min="0" {f'value="{row.fact}"' if row.fact is not None else ""}>'
                ids.append(f'fact_{row.id}')
            else:
                fact = f'<p>{row.plan if row.plan is not None else ""}</p>'
        else:
            plan = f'<p>{row.plan if row.plan is not None else ""}</p>'
            fact = f'<p>{row.fact if row.fact is not None else ""}</p>'
        form[row.section.name][row.dk_level]['plan'][row.month.month-1] = plan
        form[row.section.name][row.dk_level]['fact'][row.month.month-1] = fact
    return form, ids