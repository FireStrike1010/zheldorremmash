from app import cache, db
from models import Users, Facilities
from app import bcrypt
from secrets import token_hex
from datetime import datetime, timezone
from copy import deepcopy
from flask.sessions import SecureCookieSession
from typing import Self, NoReturn, Optional, Dict, Any

class User:
    @staticmethod
    def _get_from_db(username: str, password: str) -> Users | None:
        db_user = Users.query.filter_by(username=username).first()
        if db_user and bcrypt.check_password_hash(db_user.password, password):
            return db_user

    def _create_self_from_db(self, user: Users) -> None:
        self.username: str = user.username
        if cache.has(f'User:{self.username}'):
            self.session_keys: set = cache.get(f'User:{self.username}')['session_keys']
        else:
            self.session_keys: set = set()
        self.admin: bool = user.admin
        self.name: str = user.name
        self.surname: str = user.surname
        self.patronymic: str = user.patronymic
        self.plan_edit_permission: bool = user.plan_edit_permission
        self.fact_edit_permission: bool = user.fact_edit_permission
        self.all_months_edit_permission: bool = user.all_months_edit_permission
        facility_permissions = []
        facilities = Facilities.query.filter(Facilities.val_name != 'general').all()
        for row in facilities:
            if getattr(user, row.val_name):
                facility_permissions.append([row.val_name, row.eng_name, row.rus_name])
        self.facility_permissions = facility_permissions

    
    @staticmethod
    def _get_from_cache(username: str, session_key: str) -> Self | None:
        cache_user = cache.get(f'User:{username}')
        if cache_user and session_key in cache_user.get('session_keys', set()):
            return cache_user

    def _create_self_from_cache(self, user: Dict[str, Any]) -> None:
        self.username: str = user.get('username', '')
        self.session_keys: set = user.get('session_keys', set())
        self.admin: bool = user.get('admin', False)
        self.name: str = user.get('name', '')
        self.surname: str = user.get('surname', '')
        self.patronymic: str = user.get('patronymic', '')
        self.plan_edit_permission: bool = user.get('plan_edit_permission', False)
        self.fact_edit_permission: bool = user.get('fact_edit_permission', False)
        self.all_months_edit_permission: bool = user.get('all_months_edit_permission', False)
        self.facility_permissions: list = user.get('facility_permissions', [])
    
    def _save_to_cache(self) -> None:
        cache_user = {}
        cache_user['username'] = self.username
        cache_user['session_keys'] = self.session_keys
        cache_user['admin'] = self.admin
        cache_user['name'] = self.name
        cache_user['surname'] = self.surname
        cache_user['patronymic'] = self.patronymic
        cache_user['plan_edit_permission'] = self.plan_edit_permission
        cache_user['fact_edit_permission'] = self.fact_edit_permission
        cache_user['all_months_edit_permission'] = self.all_months_edit_permission
        cache_user['facility_permissions'] = self.facility_permissions
        cache.set(f'User:{self.username}', deepcopy(cache_user))
    
    def login(self, username: str, password: str, session: SecureCookieSession) -> None | NoReturn:
        db_user = self._get_from_db(username=username, password=password)
        if db_user is None:
            raise ValueError('Wrong username or password.')
        db_user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        self._create_self_from_db(user=db_user)
        self.record_session(session=session)
        self._save_to_cache()

    def validate(self, session: SecureCookieSession) -> None | NoReturn:
        username = session.get('username')
        if username is None:
            raise LookupError('Empty user session.')
        cache_user = self._get_from_cache(username=username, session_key=session.get('session_key'))
        if cache_user is None:
            raise ValueError('User session expired.')
        self._create_self_from_cache(user=cache_user)

    def record_session(self, session: SecureCookieSession) -> None:
        session.clear()
        session['logged_in'] = True
        session['username'] = self.username
        session['name'] = self.name
        session['surname'] = self.surname
        session['patronymic'] = self.patronymic
        session['admin'] = self.admin
        session_key = token_hex(16)
        session['session_key'] = session_key
        self.session_keys.add(session_key)
        session['facility_permissions'] = self.facility_permissions

    def __init__(self, session: SecureCookieSession,
                 username: Optional[str] = None,
                 password: Optional[str] = None) -> None:
        if username is None and password is None:
            self.validate(session=session)
        else:
            self.login(username=username, password=password, session=session)

    def logout(self, session: SecureCookieSession) -> None:
        session_key = session.get('session_key')
        if session_key in self.session_keys:
            self.session_keys.remove(session_key)
            self._save_to_cache()
