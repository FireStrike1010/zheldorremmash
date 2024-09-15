from flask import Blueprint, render_template, redirect, url_for, flash, session, g
from forms import signin_form, signup_form
from models import Users, db
from user import User
from app import bcrypt, cache


auth = Blueprint('auth', __name__, template_folder='../templates', static_folder='../static')

@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    form = signin_form()
    if form.validate_on_submit():
        try:
            user = User(session=session, username=form.username.data, password=form.password.data)
            flash('Вход выполнен.', category='success')
            return redirect(url_for('base.index'))
        except ValueError:
            flash('Неверный логин или пароль.', category='danger')
    return render_template('auth/signin.html', form=form)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if not g.user.admin:
        return redirect(url_for(auth.signin))
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
        try:
            db.session.add(user)
            db.session.commit()
            flash('Пользователь создан.', category='success')
            cache.delete(form.username.data)
        except:
            flash('Ошибка добавления пользователя в базу данных.', category='danger')
    return render_template('auth/signup.html', form=form)

@auth.route('/logout', methods=['GET'])
def logout():
    g.user.logout(session=session)
    session.clear()
    flash('Выход выполнен.', category='info')
    return redirect(url_for('auth.signin'))