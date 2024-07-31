from flask import Blueprint, session, redirect, url_for, render_template
from .auth import get_logged_in_user


base = Blueprint('base', __name__, template_folder='../templates', static_folder='../static')

@base.route('/', methods=['GET'])
def index():
    user = get_logged_in_user(session)
    if not user:
        return redirect(url_for('auth.signin'))
    return render_template('base/index.html', session=session)