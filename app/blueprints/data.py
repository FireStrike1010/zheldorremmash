from flask import Blueprint, session, redirect, url_for, render_template, request, g, session, flash
from datetime import datetime
from models import *
from table_form import TableForm
from app import cache


data = Blueprint('data', __name__, template_folder='../templates', static_folder='../static')


@data.route('/table/<string:facility>/<int:year>/<string:table>', methods=['GET'])
def edit(year: int, facility: str, table: str):
    if not facility in [i[0] for i in g.user.facility_permissions]:
        return redirect(url_for('auth.signin'))
    if abs(datetime.now().year - year) > 10:
        flash('Невозможно изменять/смотреть таблицы с разницей в более 10-ти лет.', category='warning')
        return redirect(url_for('data.data_tables', facility=facility))
    facility_id, months_ids, _ = get_ids(facility=facility, year=year)
    if len(months_ids) < 12:
        Months.create_year(year)
    match table:
        case 'TargetIndicator':
            data = TargetIndicator.query.filter(TargetIndicator.facility_id == facility_id,
                                                TargetIndicator.month_id.in_(months_ids)).all()
            form = TableForm(data,
                             fields={'target_plan': {'name': 'План(цель)', 'type': 'plan'},
                                     'mandatory_plan': {'name': 'План(обяз.)', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'}},
                             main_column='section',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=0.01, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'TargetIndicator'
            session['form_csrf_token'] = form.csrf_token
            name = 'Исполнение плана мероприятий по ДК ТОС'
            columns = ['Раздел', 'План/Факт']
        case 'ActionPlanImplementation':
            data = ActionPlanImplementation.query.filter(ActionPlanImplementation.facility_id == facility_id,
                                                         ActionPlanImplementation.month_id.in_(months_ids)).all()
            form = TableForm(data,
                             fields={'plan': {'name': 'План', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'}},
                             main_column='section',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=1, field_validation_min_value=0)
            form.generate(range(1, 6), 'dk_level')
            session['form_name'] = 'ActionPlanImplementation'
            session['form_csrf_token'] = form.csrf_token
            name = 'Исполнение плана мероприятий по ДК ТОС'
            columns = ['Раздел', 'Уровень ДК', 'План/Факт']
        case 'LevelImplementation5S':
            query = LevelImplementation5S.query.join(Months).join(Facilities).join(Workshops)
            data = query.filter(Months.year == year, Facilities.val_name == facility).all()
            form = TableForm(data, fields={'plan': {'name': 'План', 'type': 'plan'},
                                           'fact': {'name': 'Факт', 'type': 'fact'}},
                                   main_column='workshop',
                                   fact_edit_permission=g.user.fact_edit_permission,
                                   plan_edit_permission=g.user.plan_edit_permission,
                                   all_months_edit_permission=g.user.all_months_edit_permission,
                                   field_step=0.01, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'LevelImplementation5S'
            session['form_csrf_token'] = form.csrf_token
            name = 'Уровень внедрения инструмента 5С'
            columns = ['ЦЕХ', 'План/Факт']
        case 'TRMImplementation':
            data = TRMImplementation.query.filter(TRMImplementation.facility_id == facility_id,
                                                  TRMImplementation.month_id.in_(months_ids)).all()
            form = TableForm(data,
                             fields={'plan': {'name': 'План', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'}},
                             main_column='company',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=1, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'TRMImplementation'
            session['from_csrf_token'] = form.csrf_token
            name = 'Внедрение ТРМ на заводе'
            columns = ['Предприятие', 'План/Факт']
        case 'SMEDImplementation':
            data = SMEDImplementation.query.filter(SMEDImplementation.facility_id == facility_id,
                                                   SMEDImplementation.month_id.in_(months_ids)).all()
            form = TableForm(data,
                             fields={'plan': {'name': 'План', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'},
                                     'time': {'name': 'Сокр. Вр.', 'type': 'fact'}},
                             main_column='company',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=1, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'SMEDImplementation'
            session['form_csrf_token'] = form.csrf_token
            name = 'Внедрение SMED на заводе'
            columns = ['Предприятие', 'План/Факт']
        case 'SOKImplementation':
            data = SOKImplementation.query.filter(SOKImplementation.facility_id == facility_id,
                                                  SOKImplementation.month_id.in_(months_ids)).all()
            form = TableForm(data,
                             fields={'plan': {'name': 'План', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'}},
                             main_column='company',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=1, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'SOKImplementation'
            session['form_csrf_token'] = form.csrf_token
            name = 'Внедрение СОКов на заводе'
            columns = ['Предприятие', 'План/Факт']
        case 'ConductingTraining':
            data = ConductingTraining.query.filter(ConductingTraining.facility_id == facility_id,
                                                   ConductingTraining.month_id.in_(months_ids)).all()
            form = TableForm(data,
                             fields={'plan': {'name': 'План', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'}},
                             main_column='company',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=1, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'ConductingTraining'
            session['form_csrf_token'] = form.csrf_token
            name = 'Проведение обучения'
            columns = ['Предприятие', 'План/Факт']
        case 'KaizenActivities':
            data = KaizenActivities.query.filter(KaizenActivities.facility_id == facility_id,
                                                 KaizenActivities.month_id.in_(months_ids)).all()
            form = TableForm(data,
                             fields={'plan': {'name': 'План', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'}},
                             main_column='workshop',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=1, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'KaizenActivities'
            session['form_csrf_token'] = form.csrf_token
            name = 'Кайдзен деятельность (ППУ), шт.'
            columns = ['ЦЕХ', 'План/Факт']
        case 'RegulationsAdaptation':
            data = RegulationsAdaptation.query.filter(RegulationsAdaptation.facility_id == facility_id,
                                                      RegulationsAdaptation.month_id.in_(months_ids)).all()
            form = TableForm(data=data,
                             fields={'plan': {'name': 'План', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'}},
                             main_column='company',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=1, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'RegulationsAdaptation'
            session['form_csrf_token'] = form.csrf_token
            name = 'Адаптация регламентов'
            columns = ['Предприятие', 'План/Факт']
        case 'KPSCCompilation':
            data = KPSCCompilation.query.filter(KPSCCompilation.facility_id == facility_id,
                                                KPSCCompilation.month_id.in_(months_ids)).all()
            form = TableForm(data=data,
                             fields={'plan': {'name': 'План', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'}},
                             main_column='workshop',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=1, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'KPSCCompilation'
            session['form_csrf_token'] = form.csrf_token
            name = 'Составление КПСЦ'
            columns = ['Цех', 'План/Факт']
        case 'SVMImplementation':
            data = SVMImplementation.query.filter(SVMImplementation.facility_id == facility_id,
                                                  SVMImplementation.month_id.in_(months_ids)).all()
            form = TableForm(data=data,
                             fields={'plan': {'name': 'План', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'}},
                             main_column='company',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=1, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'SVMImplementation'
            session['form_csrf_token'] = form.csrf_token
            name = 'Внедрение СВМ'
            columns = ['Предприятие', 'План/Факт']
        case 'ExperienceExchange':
            data = ExperienceExchange.query.filter(ExperienceExchange.facility_id == facility_id,
                                                   ExperienceExchange.month_id.in_(months_ids)).all()
            form = TableForm(data=data,
                             fields={'plan': {'name': 'План', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'}},
                             main_column='company',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=1, field_validation_min_value=0)
            form.generate()
            session['form_name'] = 'ExperienceExchange'
            session['form_csrf_token'] = form.csrf_token
            name = 'Обмен опытом'
            columns = ['Предприятие', 'План/Факт']
        case 'PSZ':
            data = PSZ.query.filter(PSZ.facility_id == facility_id,
                                    PSZ.month_id.in_(months_ids)).all()
            form = TableForm(data=data,
                             fields={'target_plan': {'name': 'План (цель)', 'type': 'plan'},
                                     'mandatory_plan': {'name': 'План (обяз.)', 'type': 'plan'},
                                     'fact': {'name': 'Факт', 'type': 'fact'},
                                     'effect': {'name': 'Эффект по Инициативам', 'type': 'fact'}},

                             main_column='company',
                             fact_edit_permission=g.user.fact_edit_permission,
                             plan_edit_permission=g.user.plan_edit_permission,
                             all_months_edit_permission=g.user.all_months_edit_permission,
                             field_step=0.1, field_validation_min_value=0.0)
            form.generate()
            session['form_name'] = 'PSZ'
            session['form_csrf_token'] = form.csrf_token
            name = 'ПСЗ, млн. руб.'
            columns = ['Предприятие', 'План/Факт']
        case _:
            flash(f'Таблицы {table} не существует.', category='danger')
            return redirect(url_for('data.data_tables', facility=facility))
    return render_template('data/TableForm.html',
                           facility=facility, year=year,
                           table=table,
                           name=name, columns=columns,
                           fields_type=form.fields, form=form.form)

@data.route('/data_tables/<string:facility>', methods=['GET'])
def data_tables(facility: str):
    if not facility in [i[0] for i in g.user.facility_permissions]:
        return redirect(url_for('auth.signin'))
    return render_template('data/tables.html', facility=facility, year=datetime.now().year)

@data.route('/table/<string:facility>/<int:year>/<string:table>', methods=['POST'])
def save_table(facility: str, year: int, table: str):
    if not facility in [i[0] for i in g.user.facility_permissions]:
        return redirect(url_for('auth.signin'))
    response = redirect(url_for('data.edit', facility=facility, year=year, table=table))
    if not cache.has(f"Form:{session.get('form_csrf_token')}"):
        flash('Ваша сессия устарела, данные не сохранены. Пожалуйста обновите страницу и заполните заново.', category='danger')
        return response
    old_form = cache.get(f"Form:{session['form_csrf_token']}")
    try:
        changed_data, changed_form = TableForm._validate(old_form_data=old_form, user_csrf_token=session['form_csrf_token'], form_data=request.form)
        cache.set(f"Form:{session['form_csrf_token']}", changed_form)
    except ConnectionRefusedError:
        flash('Неверный CSRF токен.', category='danger')
        return response
    except (PermissionError, ValueError):
        flash('HPP здесь не работает...', category='danger')
        return response
    except MemoryError:
        flash('Ошибка сервера. Пожалуйста обновите страницу и заполните заново. Возможно это поможет...', category='alert-danger')
        return response
    model = globals().get(session.get('form_name'))
    if model is None:
        flash(f'Таблица {session.get('form_name')} не существует.', category='danger')
        return response
    try:
        save_form(model, changed_data)
        cache.delete(f"Form:{session['form_csrf_token']}")
        session.pop('form_csrf_token')
        session.pop('form_name')
        flash('Изменения сохранены.', category='info')
        return response
    except:
        flash('Неизвестная ошибка. Данные не сохранены.', 'danger')
        return response