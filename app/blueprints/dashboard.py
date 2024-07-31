from flask import Blueprint
from flask import render_template


dashboard = Blueprint('dashboard', __name__, template_folder='../templates', static_folder='../static')

@dashboard.route('/dashboard/<string:facility>', methods=['GET'])
def facility_dashboard(facility: str):
    return f'dashboard {facility}'