from uuid import uuid4
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, session
from forms import signin_form, signup_form
from models import Users, db
from app import bcrypt
from facilities import facilities


def generate_session_key():
    return uuid4().hex

def get_logged_in_user(user_session):
    if 'username' not in user_session:
        return False
    user = Users.query.filter_by(username=user_session.get('username')).first()
    if user_session.get('logged_in') and user_session.get('session_key'):
        if user_session['session_key'] == user.session_key and (datetime.now(timezone.utc) - user.last_login).days == 0:
            return user
    user_session.clear()
    return False

def record_session(user_session, user: Users):
    user_session['logged_in'] = True
    user_session['username'] = user.username
    user_session['name'] = user.name
    user_session['surname'] = user.surname
    user_session['patronymic'] = user.patronymic
    user_session['admin'] = user.admin
    
    facility_permissions = []
    for db_name, name in facilities.items():
        if getattr(user, db_name):
            facility_permissions.append([name, db_name])
    user_session['facility_permissions'] = facility_permissions


auth = Blueprint('auth', __name__, template_folder='../templates', static_folder='../static')

@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    form = signin_form()
    if form.validate_on_submit():
        username = form.username.data
        user = Users.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            record_session(session, user)
            session_key = generate_session_key()
            session['session_key'] = session_key
            user.session_key = session_key
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            flash('Вход выполнен.', category='success')
            return redirect(url_for('base.index'))
        else:
            flash('Неверный логин или пароль.', category='warning')
    return render_template('auth/signin.html', form=form)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    user = get_logged_in_user(session)
    if not user or not user.admin:
        return redirect(url_for('auth.signin'))
    form = signup_form()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode()
        user = Users(username=form.username.data, name=form.name.data, surname=form.surname.data,
                     patronymic=form.patronymic.data, password=hashed_password,
                     facility_ULRZ=form.facility_ULRZ.data,
                     facility_UULVRZ=form.facility_UULVRZ.data,
                     facility_OLRZ=form.facility_OLRZ.data,
                     facility_CHERZ=form.facility_CHERZ.data,
                     facility_ATRZ=form.facility_ATRZ.data,
                     facility_RERZ=form.facility_RERZ.data,
                     facility_VTRZ=form.facility_VTRZ.data,
                     facility_YAERZ=form.facility_YAERZ.data,
                     facility_AU=form.facility_AU.data,
                     plan_edit_permission=form.plan_edit_permission.data,
                     fact_edit_permission=form.fact_edit_permission.data,
                     all_months_edit_permission=form.all_months_edit_permission.data)
        db.session.add(user)
        db.session.commit()
        flash('Пользователь создан.', category='message')
    else:
         flash('Ошибка.', category='warning')
    return render_template('auth/signup.html', form=form)

@auth.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('auth.signin'))