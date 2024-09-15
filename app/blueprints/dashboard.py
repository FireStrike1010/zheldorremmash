from flask import Blueprint, render_template, redirect, url_for, flash, g
from datetime import datetime
from models import get_ids
from graphs import *

dashboard = Blueprint('dashboard', __name__, template_folder='../templates', static_folder='../static')

@dashboard.route('/dashboard/<string:facility>/<int:year>', methods=['GET'])
def facility_dashboard(facility: str, year: int):
    if abs(datetime.now().year - year) > 10:
        flash('Невозможно смотреть дашборды с разницей в более 10-ти лет.', category='warning')
        return redirect(url_for('base.index'))
    facility_name = Facilities.query.filter(Facilities.val_name == facility).first().rus_name
    facility_id, months_ids, month_id = get_ids(facility=facility, year=year)
    if year != datetime.now().year:
        month_id = months_ids
    target_indicator = plot_TargetIndicator(facility_id=facility_id, months_ids=months_ids).to_json()
    target_indicator_pie = plot_TargetIndicator_pie(facility_id=facility_id, month_id=month_id).to_json()
    action_plan_implementation = plot_ActionPlanImplementation(facility_id=facility_id, months_ids=months_ids).to_json()
    action_plan_implementation_pie = plot_ActionPlanImplementation_pie(facility_id=facility_id, month_id=month_id).to_json()
    return render_template('Dashboard.html', facility_name=facility_name, year=year,
                           target_indicator=target_indicator, target_indicator_pie=target_indicator_pie,
                           action_plan_implementation=action_plan_implementation, action_plan_implementation_pie=action_plan_implementation_pie,
                           )