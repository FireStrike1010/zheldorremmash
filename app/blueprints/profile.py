from flask import Blueprint, session, redirect, url_for, render_template, flash
from .auth import get_logged_in_user
from models import Users, db
from forms import profile_edit_form, change_password_form
from app import bcrypt

def get_users_list():
    users = Users.query.order_by(Users.surname, Users.name, Users.patronymic).all()
    return users
    

profile = Blueprint('profile', __name__, template_folder='../templates', static_folder='../static')

    
@profile.route('/users_list', methods=['GET'])
def users_list():
    user = get_logged_in_user(session)
    if not user or not user.admin:
        redirect(url_for('auth.signin'))
    users = get_users_list()
    return render_template('profile/users_list.html', session=session, users=users)

@profile.route('/profile/<string:username>', methods=['GET', 'POST'])
def profile_edit(username: str):
    user = get_logged_in_user(session)
    queried_user = Users.query.filter_by(username=username).first()
    if not user or not queried_user:
        return redirect(url_for('auth.signin'))
    if queried_user.username == username or user.admin:
        form = profile_edit_form(name=queried_user.name,
                                 surname=queried_user.surname,
                                 patronymic=queried_user.patronymic,
                                 plan_edit_permission=queried_user.plan_edit_permission,
                                 fact_edit_permission=queried_user.fact_edit_permission,
                                 all_months_edit_permission=queried_user.all_months_edit_permission,
                                 facility_ULRZ=queried_user.facility_ULRZ,
                                 facility_UULVRZ=queried_user.facility_UULVRZ,
                                 facility_OLRZ=queried_user.facility_OLRZ,
                                 facility_CHERZ=queried_user.facility_CHERZ,
                                 facility_ATRZ=queried_user.facility_ATRZ,
                                 facility_RERZ=queried_user.facility_RERZ,
                                 facility_VTRZ=queried_user.facility_VTRZ,
                                 facility_YAERZ=queried_user.facility_YAERZ,
                                 facility_AU=queried_user.facility_AU)
        if form.validate_on_submit():
            queried_user.name = form.name.data
            queried_user.surname = form.surname.data
            queried_user.patronymic = form.patronymic.data
            if user.admin:
                queried_user.plan_edit_permission = form.plan_edit_permission.data
                queried_user.fact_edit_permission = form.fact_edit_permission.data
                queried_user.all_months_edit_permission = form.all_months_edit_permission.data
                queried_user.facility_ULRZ = form.facility_ULRZ.data
                queried_user.facility_UULVRZ = form.facility_UULVRZ.data
                queried_user.facility_OLRZ = form.facility_OLRZ.data
                queried_user.facility_CHERZ = form.facility_CHERZ.data
                queried_user.facility_ATRZ = form.facility_ATRZ.data
                queried_user.facility_RERZ = form.facility_RERZ.data
                queried_user.facility_VTRZ = form.facility_VTRZ.data
                queried_user.facility_YAERZ = form.facility_YAERZ.data
                queried_user.facility_AU = form.facility_AU.data
            db.session.commit()
            flash('Изменения сохранены', category='info')
            if user.admin:
                return redirect(url_for('profile.users_list'))
            else:
                return redirect(url_for('base.index'))
        return render_template('profile/profile.html', form=form, user=user, queried_user=queried_user, session=session)
    else:
        return redirect(url_for('auth.signin'))

@profile.route('/delete/<string:username>', methods=['GET'])
def delete(username: str):
    user = get_logged_in_user(session)
    if not user or not user.admin:
        return redirect(url_for('auth.signin'))
    queried_user = Users.query.filter_by(username=username).first()
    if not queried_user.admin:
        db.session.delete(queried_user)
        db.session.commit()
        flash(f'Пользователь {username} удален.', category='info')
        return redirect(url_for('profile.users_list'))

@profile.route('/change_password/<string:username>', methods=['GET', 'POST'])
def change_password(username: str):
    user = get_logged_in_user(session)
    if not user or not (user.username == username or user.admin):
        return redirect(url_for('auth.signin'))
    queried_user = Users.query.filter_by(username=username).first()
    form = change_password_form()
    if form.validate_on_submit():
        if user.admin or bcrypt.check_password_hash(queried_user.password, form.old_password.data):
            hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode()
            queried_user.password = hashed_password
            db.session.commit()
            flash('Пароль изменен.', category='info')
            if queried_user.username == user.username:
                print(queried_user.username, user.username)
                session.clear()
                return redirect(url_for('auth.signin'))
            else:
                return redirect(url_for('profile.users_list'))
        else:
            flash('Неверный старый пароль', category='error')
            return redirect(url_for('profile.change_password', username=username))
    return render_template('profile/change_password.html', form=form, user=user, username=queried_user.username)