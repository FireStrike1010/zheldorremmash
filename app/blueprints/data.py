from flask import Blueprint, session, redirect, url_for, render_template, request
from datetime import datetime
from .auth import get_logged_in_user
from models import *
from forms import generate_target_indicator, generate_action_plan_implementation
from creating_tables import create_year, generate_sql_table


def write_data(table, ids: list[str], request) -> None:
    for field in ids:
        field_data = request.form.get(field)
        field_data = None if field_data == '' else float(field_data)
        if field_data is not None:
            field_name, field_id = field.rsplit('_', 1)
            field_id = int(field_id)
            row = table.query.get_or_404(field_id)
            setattr(row, field_name, field_data)
            db.session.commit()

data = Blueprint('data', __name__, template_folder='../templates', static_folder='../static')


@data.route('/data/<string:facility>/<int:year>/<string:table>', methods=['GET', 'POST'])
def edit(year: int, facility: str, table: str):
    user = get_logged_in_user(session)
    if not user or not getattr(user, facility):
        return redirect(url_for('auth.signin'))
    if len(Months.query.filter(Months.year == year).all()) == 0:
        create_year(year)
        generate_sql_table(TargetIndicator, [SectionsTargetIndicator], [('section_id', 'id')], year)
        generate_sql_table(ActionPlanImplementation, [SectionsTargetIndicator], [('section_id', 'id')], year, iterator=range(1, 6), iterator_column_name='dk_level')
    match table:
        case 'TargetIndicator':
            query = TargetIndicator.query.join(Months).join(Facilities).join(SectionsTargetIndicator)
            data = query.filter(Months.year == year, Facilities.val_name == facility).order_by(SectionsTargetIndicator.name, Months.month).all()
            form, ids = generate_target_indicator(data, user.fact_edit_permission, user.plan_edit_permission, user.all_months_edit_permission)
            if request.method == 'POST':
                write_data(TargetIndicator, ids=ids, request=request)
                return redirect(url_for('data.data_tables', facility=facility))
            return render_template('data/TargetIndicator.html', form=form)
        case 'ActionPlanImplementation':
            query = ActionPlanImplementation.query.join(Months).join(Facilities).join(SectionsTargetIndicator)
            data = query.filter(Months.year == year, Facilities.val_name == facility).order_by(SectionsTargetIndicator.name, ActionPlanImplementation.dk_level, Months.month).all()
            form, ids = generate_action_plan_implementation(data, user.fact_edit_permission, user.plan_edit_permission, user.all_months_edit_permission)
            if request.method == 'POST':
                write_data(ActionPlanImplementation, ids=ids, request=request)
                return redirect(url_for('data.data_tables', facility=facility))
            return render_template('data/ActionPlanImplementation.html', form=form)
        case _:
            return redirect(url_for('data.data_tables', facility=facility))

@data.route('/data_tables/<string:facility>', methods=['GET'])
def data_tables(facility: str):
    user = get_logged_in_user(session)
    if not user or not getattr(user, facility):
        return redirect(url_for('auth.signin'))
    return render_template('data/tables.html', facility=facility, year=datetime.now().year)