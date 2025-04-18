from fastapi import Request, HTTPException, Header
from typing import NoReturn, Literal, List, Annotated, Optional
from fastapi import Depends
from database.users import UsersOrm, UserSchema
import os

def get_session_key(api_session_key: Annotated[str, Header()]):
    return api_session_key

async def get_current_user(session_key: str, userorm: UsersOrm) -> UserSchema | NoReturn:
    try:
        user = await userorm.validate_session_key(session_key)
    except ValueError:
        raise HTTPException(401, 'Invalid session key, try re-login to api to acquire one')
    return user

async def verify_role(session_key: str,
                      userorm: UsersOrm,
                      possible_roles: List[Literal['Admin', 'Moderator', 'Auditor', 'User']]) -> None | NoReturn:
    user = await get_current_user(session_key, userorm)
    if user['role'] not in possible_roles:
        raise HTTPException(403, f"You don't have that privilege, you must be in {possible_roles}")