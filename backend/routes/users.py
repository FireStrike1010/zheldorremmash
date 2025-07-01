from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from pydantic import ValidationError
import asyncio
from models.users import AddUserRequest, UserResponse, UpdateUserRequest, DeleteManyRequest
from database import User
from utils.password_hasher import hash_password
from utils.session_validator import verify_role, get_session_key, get_current_user
from typing import List

router = APIRouter(prefix='/users', tags=['Users'])

@router.post('/add', response_model=UserResponse)
async def add(data: AddUserRequest, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin'])
    try:
        user = await User.add_one(data)
        return UserResponse.model_validate(user)
    except DuplicateKeyError as e:
        raise HTTPException(409, detail=str(e))

@router.get('/@{username}', response_model=UserResponse)
async def get(username: str, session_key: str = Depends(get_session_key)):
    await verify_role(session_key)
    try:
        user = await User.get_one_by_username(username)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

@router.delete('/@{username}')
async def delete(username: str, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin'])
    try:
        user = await User.get_one_by_username(username)
        await user.delete()
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

@router.delete('/delete_many')
async def delete_many(data: DeleteManyRequest, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin'])
    try:
        users = await asyncio.gather(
            *[User.get_one_by_username(username) for username in data.usernames],
            return_exceptions=True)
        await asyncio.gather(*[user.delete() for user in users])
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

@router.patch('/@{username}', response_model=UserResponse)
async def patch(username: str, data: UpdateUserRequest, session_key: str = Depends(get_session_key)):
    current_user = await get_current_user(session_key)
    if current_user.role == 'Admin' or current_user.username == username:
        try:
            user = await User.get_one_by_username(username)
        except ValueError as e:
            raise HTTPException(404, detail=str(e))
        data = data.model_dump(exclude_none=True)
        if any(field in ('username', 'email', 'role', 'job_title', 'password') for field in data.keys()) and current_user.role != 'Admin':
            raise HTTPException(403, "You don't have that privilege, you must be Admin")
        if 'password' in data.keys():
            data['password'] = hash_password(data['password'])
        try:
            await user.update_params(**data)
            return UserResponse.model_validate(user)
        except ValidationError as e:
            raise HTTPException(400, detail=str(e))
    else:
        raise HTTPException(403, "You don't have that privilege, you must be Admin or this user")

@router.get('/', response_model=List[UserResponse])
async def get_all(session_key: str = Depends(get_session_key)):
    await verify_role(session_key)
    users = await User.get_all()
    users = [UserResponse.model_validate(user) for user in users]
    return users