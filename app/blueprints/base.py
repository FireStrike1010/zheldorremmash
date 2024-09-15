from flask import Blueprint, session, render_template
from datetime import datetime


base = Blueprint('base', __name__, template_folder='../templates', static_folder='../static')

@base.route('/', methods=['GET'])
def index():
    return render_template('base/index.html', session=session, year=datetime.now().year)