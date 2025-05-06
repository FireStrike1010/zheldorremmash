from fastapi import HTTPException, Header
from typing import NoReturn, List, Annotated, get_args
from datetime import datetime
from database import User
from database.users import Roles
import os

def get_session_key(api_session_key: Annotated[str, Header(default_factory=str)]):
    return api_session_key

async def get_current_user(session_key: str) -> User | NoReturn:
    if session_key == os.getenv('MASTER_KEY'):
        return User(username='DungeonMaster',
                    email='master@dungeon.com',
                    name='Master',
                    surname='God',
                    role='Admin',
                    created_at=datetime.now(),
                    password='')
    try:
        user = await User.get_one_by_session_key(session_key)
    except ValueError:
        raise HTTPException(401, 'Invalid session key, try re-login to api to acquire one')
    return user

async def verify_role(session_key: str, possible_roles: List[Roles] = list(get_args(Roles))) -> None | NoReturn:
    if session_key == os.getenv('MASTER_KEY'):
        return
    try:
        user_role = await User.validate_access(session_key)
    except ValueError:
        raise HTTPException(401, 'Invalid session key, try re-login to api to acquire one')
    if user_role not in possible_roles:
        raise HTTPException(403, f"You don't have that privilege, you must be {possible_roles}")