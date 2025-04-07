from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import asyncio
from models.users import AddUserRequest, AddUserResponse, User, UpdateUserRequest, DeleteManyRequest
from database.users import UserSchema, UsersOrm
from utils.password_hasher import hash_password
from utils.session_validator import verify_role, get_session_key, get_current_user
from utils.pydanctic_utils import pass_fields
from typing import List

router = APIRouter(prefix='/users', tags=['Users'])

@router.post('/add', response_model=AddUserResponse)
async def add(data: AddUserRequest,
              session_key: str = Depends(get_session_key),
              userorm: UsersOrm = Depends(UsersOrm.get_orm)):
    await verify_role(session_key, userorm, possible_roles=['Admin'])
    data.password = hash_password(data.password)
    user = UserSchema(**data.model_dump(), created_at=datetime.now())
    try:
        user = await userorm.add_one(user)
    except DuplicateKeyError as e:
        raise HTTPException(409, detail=str(e))
    return AddUserResponse(_id=user.id, created_at=user.created_at)

@router.get('/@{username}', response_model=User)
async def get(username: str,
              session_key: str = Depends(get_session_key),
              userorm: UsersOrm = Depends(UsersOrm.get_orm)):
    await get_current_user(session_key, userorm)
    user = await userorm.get_one_by(username=username)
    if not user:
        raise HTTPException(404, f"User not found")
    return pass_fields(User, user)

@router.delete('/@{username}')
async def delete(username: str,
                 session_key: str = Depends(get_session_key),
                 userorm: UsersOrm = Depends(UsersOrm.get_orm)):
    await verify_role(session_key, userorm, ['Admin'])
    try:
        await userorm.delete_by_username(username)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    return

@router.delete('/delete_many')
async def delete_many(data: DeleteManyRequest,
                      session_key: str = Depends(get_session_key),
                      userorm: UsersOrm = Depends(UsersOrm.get_orm)):
    await verify_role(session_key, userorm, possible_roles=['Admin'])
    try:
        await asyncio.gather(*(userorm.delete_by_username(username) for username in data.usernames))
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    return

@router.patch('/@{username}', response_model=User)
async def patch(username: str,
                data: UpdateUserRequest,
                session_key: str = Depends(get_session_key),
                userorm: UsersOrm = Depends(UsersOrm.get_orm)):
    current_user = await get_current_user(session_key, userorm)
    data = data.model_dump(exclude_none=True)
    if current_user['role'] == 'Admin':
        try:
            user = await userorm.update_by_username(username, kwargs=data)
            return pass_fields(User, user)
        except ValueError as e:
            raise HTTPException(404, detail=str(e))
    elif current_user['username'] == username:
        if any(k in ['username', 'email', 'password', 'role', 'job_title'] for k in data.keys()):
            raise HTTPException(403, f"You don't have that privilege, you must be admin")
        try:
            user = await userorm.update_by_username(username, kwargs=data)
            return pass_fields(User, user)
        except ValueError as e:
            raise HTTPException(404, detail=str(e))
    else:
        raise HTTPException(404, detail=str(e))

@router.get('/', response_model=List[User])
async def get_all(session_key: str = Depends(get_session_key),
                  userorm: UsersOrm = Depends(UsersOrm.get_orm)):
    await verify_role(session_key, userorm, ['Admin', 'Moderator'])
    users = await userorm.get_all()
    users = [pass_fields(User, user) for user in users]
    return users