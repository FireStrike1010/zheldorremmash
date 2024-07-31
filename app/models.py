from app import db
from sqlalchemy.sql import func, false
from datetime import datetime


class Users(db.Model):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80))
    surname = db.Column(db.String(80))
    patronymic = db.Column(db.String(80))
    password = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)
    session_key = db.Column(db.String(80))
    admin = db.Column(db.Boolean, nullable=False, default=False, server_default=false())

    plan_edit_permission = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    fact_edit_permission = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    all_months_edit_permission = db.Column(db.Boolean, nullable=False, default=False, server_default=false())

    facility_ULRZ = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    facility_UULVRZ = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    facility_OLRZ = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    facility_CHERZ = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    facility_ATRZ = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    facility_RERZ = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    facility_VTRZ = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    facility_YAERZ = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    facility_AU = db.Column(db.Boolean, nullable=False, default=False, server_default=false())

    def __repr__(self) -> str:
        return f'<User {self.username}>'
    
    def get_fio(self) -> str:
        return f'{self.surname} {self.name} {self.patronymic}'


class Months(db.Model):
    '''
    Таблица с месяцами как id (вспомогательная таблица)
    '''
    __tablename__ = 'Months'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False, default=datetime.now().year)
    month = db.Column(db.Integer, nullable=False, default=datetime.now().month)

class Facilities(db.Model):
    '''
    Таблица с заводами как id (вспомогательная таблица)
    '''
    __tablename__ = 'Facilities'
    id = db.Column(db.Integer, primary_key=True)
    eng_name = db.Column(db.String(80), nullable=False)
    rus_name = db.Column(db.String(80), nullable=False)
    val_name = db.Column(db.String(80), nullable=False)

class TargetIndicator(db.Model):
    '''
    Достижение целевого показателя по ДК ТОС (первая таблица)
    '''
    __tablename__ = 'TargetIndicatorDKTOS'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    section_id = db.Column(db.Integer, db.ForeignKey('SectionsTargetIndicatorDKTOS.id'), nullable=False)
    section = db.relationship('SectionsTargetIndicator')
    target_plan = db.Column(db.Float)
    mandatory_plan = db.Column(db.Float)
    fact = db.Column(db.Float)

class SectionsTargetIndicator(db.Model):
    '''
    Разделы для достижение целевого показателя по ДК ТОС как id (вспомогательная таблица)
    '''
    __tablename__ = 'SectionsTargetIndicatorDKTOS'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

class ActionPlanImplementation(db.Model):
    '''
    Исполнение плана мероприятий по ДК ТОС (вторая таблица)
    '''
    __tablename__ = 'ActionPlanImplementation'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    section_id = db.Column(db.Integer, db.ForeignKey('SectionsTargetIndicatorDKTOS.id'), nullable=False)
    section = db.relationship('SectionsTargetIndicator')
    dk_level = db.Column(db.Integer, nullable=False)
    plan = db.Column(db.Integer)
    fact = db.Column(db.Integer)

class LevelImplementation5S(db.Model):
    '''
    Уровень внедрения инструмента 5С (третья таблица)
    '''
    __tablename__ = 'LevelImplementation5S'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    workshop_id = db.Column(db.Integer, db.ForeignKey('Workshops.id'), nullable=False)
    workshop = db.relationship('Workshops')
    plan = db.Column(db.Float)
    fact = db.Column(db.Float)

class Workshops(db.Model):
    '''
    Цеха для уровень внедрения инструмента 5С, Кайдзен деятельность и Составление КПСЦ как id (вспомогательная таблица)
    '''
    __tablename__ = 'Workshops'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'))
    facility = db.relationship('Facilities')
    name = db.Column(db.String(256), nullable=False)

class TRMImplementation(db.Model):
    '''
    Внедрение ТРМ на заводе (четвертая таблица)
    '''
    __tablename__ = 'TRMImplementation'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    company_id = db.Column(db.Integer, db.ForeignKey('CompanyTRMImplementation.id'), nullable=False)
    company = db.relationship('CompanyTRMImplementation')
    plan = db.Column(db.Integer)
    fact = db.Column(db.Integer)

class CompanyTRMImplementation(db.Model):
    '''
    Предприятия для внедрение ТРМ на заводе как id (вспомогательная таблица)
    '''
    __tablename__ = 'CompanyTRMImplementation'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'))
    facility = db.relationship('Facilities')
    name = db.Column(db.String(256), nullable=False)

class SMEDImplementation(db.Model):
    '''
    Внедрение SMED на заводе (пятая таблица)
    '''
    __tablename__ = 'SMEDImplementation'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    company_id = db.Column(db.Integer, db.ForeignKey('CompanySMEDImplementation.id'), nullable=False)
    company = db.relationship('CompanySMEDImplementation')
    plan = db.Column(db.Integer)
    fact = db.Column(db.Integer)
    time = db.Column(db.Float)
    

class CompanySMEDImplementation(db.Model):
    '''
    Предприятия для внедрение SMED на заводе как id (пока только одно значение) (вспомогательная таблица)
    '''
    __tablename__ = 'CompanySMEDImplementation'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'))
    facility = db.relationship('Facilities')
    name = db.Column(db.String(256), nullable=False)

class SOKImplementation(db.Model):
    '''
    Внедрение СОКов на заводе (шестая таблица)
    '''
    __tablename__ = 'SOKImplementation'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    company_id = db.Column(db.Integer, db.ForeignKey('CompanySOKImplementation.id'), nullable=False)
    company = db.relationship('CompanySOKImplementation')
    plan = db.Column(db.Integer)
    fact = db.Column(db.Integer)

class CompanySOKImplementation(db.Model):
    '''
    Предприятия для внедрение СОКов на заводе как id (пока только одно значение) (вспомогательная таблица)
    '''
    __tablename__ = 'CompanySOKImplementation'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'))
    facility = db.relationship('Facilities')
    name = db.Column(db.String(256), nullable=False)

class ConductingTraining(db.Model):
    '''
    Проведение обучения (седьмая таблица)
    '''
    __tablename__ = 'ConductingTraining'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    company_id = db.Column(db.Integer, db.ForeignKey('CompanyConductingTraining.id'), nullable=False)
    company = db.relationship('CompanyConductingTraining')
    plan = db.Column(db.Integer)
    fact = db.Column(db.Integer)

class CompanyConductingTraining(db.Model):
    '''
    Предприятия для проведение обучения как id (пока только два значения) (вспомогательная таблица)
    '''
    __tablename__ = 'CompanyConductingTraining'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

class KaizenActivities(db.Model):
    '''
    Кайдзен деятельность (ППУ), шт. (восьмая таблица)
    '''
    __tablename__ = 'KaizenActivities'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    workshop_id = db.Column(db.Integer, db.ForeignKey('Workshops.id'), nullable=False)
    workshop = db.relationship('Workshops')
    plan = db.Column(db.Integer)
    fact = db.Column(db.Integer)

class RegulationsAdaptation(db.Model):
    '''
    Адаптация регламентов (девятая таблица)
    '''
    __tablename__ = 'RegulationsAdaptation'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    company_id = db.Column(db.Integer, db.ForeignKey('CompanyRegulationsAdaptation.id'), nullable=False)
    company = db.relationship('CompanyRegulationsAdaptation')
    plan = db.Column(db.Integer)
    fact = db.Column(db.Integer)

class CompanyRegulationsAdaptation(db.Model):
    '''
    Предприятия для Адаптация регламентов как id (пока только одно значение) (вспомогательная таблица)
    '''
    __tablename__ = 'CompanyRegulationsAdaptation'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

class KPSCCompilation(db.Model):
    '''
    Составление КПСЦ (десятая таблица)
    '''
    __tablename__ = 'KPSCCompilation'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    workshop_id = db.Column(db.Integer, db.ForeignKey('Workshops.id'), nullable=False)
    workshop = db.relationship('Workshops')
    plan = db.Column(db.Integer)
    fact = db.Column(db.Integer)

class SVMImplementation(db.Model):
    '''
    Внедрение СВМ (одиннадцатая таблица)
    '''
    __tablename__ = 'SVMImplementation'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    company_id = db.Column(db.Integer, db.ForeignKey('CompanySVMImplementation.id'), nullable=False)
    company = db.relationship('CompanySVMImplementation')
    plan = db.Column(db.Integer)
    fact = db.Column(db.Integer)

class CompanySVMImplementation(db.Model):
    '''
    Предприятия для Внедрение СВМ как id (пока только одно значение) (вспомогательная таблица)
    '''
    __tablename__ = 'CompanySVMImplementation'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

class ExperienceExchange(db.Model):
    '''
    Обмен опытом (двенадцатая таблица)
    '''
    __tablename__ = 'ExperienceExchange'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    company_id = db.Column(db.Integer, db.ForeignKey('CompanyExperienceExchange.id'), nullable=False)
    company = db.relationship('CompanyExperienceExchange')
    plan = db.Column(db.Integer)
    fact = db.Column(db.Integer)

class CompanyExperienceExchange(db.Model):
    '''
    Предприятия для Обмен опытом как id (пока только одно значение) (вспомогательная таблица)
    '''
    __tablename__ = 'CompanyExperienceExchange'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

class PSZ(db.Model):
    '''
    ПСЗ, млн. руб. (тринадцатая таблица)
    '''
    __tablename__ = 'PSZ'
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('Facilities.id'), nullable=False)
    facility = db.relationship('Facilities')
    month_id = db.Column(db.Integer, db.ForeignKey('Months.id'), nullable=False)
    month = db.relationship('Months')
    target_plan = db.Column(db.Float)
    mandatory_plan = db.Column(db.Float)
    fact = db.Column(db.Float)
    effect = db.Column(db.Float)