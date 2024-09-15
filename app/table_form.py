from secrets import token_hex
from datetime import datetime
from typing import List, Dict, Optional, Any, NoReturn, Tuple
from collections.abc import Sequence
from app import cache


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
        self.csrf_token = token_hex(16)

    def _generate(self) -> None | NoReturn:
        self.form: Dict[Dict[str, List[str]]] = {}
        self.field_ids: Dict[str, Any] = {}
        for row in self.data:
            section: str = getattr(row, self.main_column).name
            if section not in self.form:
                self.form[section] = {i: [None]*12 for i in self.fields.keys()}
            for key, value_type in self.fields.items():
                value_type = value_type['type']
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
<p style="{self.field_style}" id="{name}">{value}</p>
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
                value_type = value_type['type']
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
<p style="{self.field_style}" id="{name}">{value}</p>
'''.replace('\n', ' ')
                self.form[section][getattr(row, level_column_name)][key][row.month.month-1] = field

    def generate(self, additional_level_range: Optional[Sequence] = None,
                 level_column_name: Optional[str] = None, sort: bool = True,
                 save_to_cache: bool = True) -> None | NoReturn:
        if additional_level_range is None:
            self._generate()
        else:
            self._generate_with_levels(additional_level_range, level_column_name)
        if sort:
            self.form = dict(sorted(self.form.items()))
        if save_to_cache:
            self._save_to_cache()
    
    def _save_to_cache(self):
        form_data = {'field_ids': self.field_ids.copy()}
        form_data['field_validation_min_value'] = self.field_validation_min_value
        form_data['field_validation_max_value'] = self.field_validation_max_value
        form_data['csrf_token'] = self.csrf_token
        cache.set(f'Form:{self.csrf_token}', form_data)

    @staticmethod
    def _validate(old_form_data: Dict[str, Any],
                  user_csrf_token: Optional[str],
                  form_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]] | NoReturn:
        changed_data: Dict[str, Any] = {}
        field_validation_min_value = old_form_data.get('field_validation_min_value')
        field_validation_max_value = old_form_data.get('field_validation_max_value')
        if not old_form_data.get('csrf_token') == user_csrf_token:
            raise ConnectionRefusedError('Wrong csrf token.')
        field_ids = old_form_data.get('field_ids')
        if field_ids is None:
            raise MemoryError('Missing old form data. Cannot validate values.')
        for field_name, field_data in form_data.items():
            value = field_ids.get(field_name)
            if value is None:
                raise PermissionError(f'{field_name} is not allowed to change for current user or not exists.')
            if field_data != '' and field_data is not None:
                if ((field_validation_min_value is not None
                     ) and (float(field_data) < field_validation_min_value)
                     ) or ((field_validation_max_value is not None
                            ) and (float(field_data) > field_validation_max_value)):
                    raise ValueError(f"Value (with id {field_name}) is out of bound ({field_validation_min_value if field_validation_min_value is not None else '-∞'} and {field_validation_max_value if field_validation_max_value is not None else '∞'})")
            if value != field_data:
                changed_data[field_name] = field_data
            else:
                old_form_data['field_ids'][field_name] = field_data
        return changed_data, old_form_data