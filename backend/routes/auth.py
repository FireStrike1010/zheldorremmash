from fastapi import APIRouter, HTTPException, Depends
from secrets import token_hex
from database.users import UsersOrm
from models.auth import LoginRequest, LoginResponse, UpdatePasswordRequest
from utils.email_validator import is_email
from utils.password_hasher import verify_password, hash_password
from utils.pydantic_utils import pass_fields
from utils.session_validator import get_current_user, get_session_key


router = APIRouter(prefix='/auth', tags=['Auth'])

@router.post('/login', response_model=LoginResponse)
async def login(data: LoginRequest, userorm: UsersOrm = Depends(UsersOrm.get_orm)):
    if is_email(data.username_or_email):
        user = await userorm.get_one_by(email=data.username_or_email)
    else:
        user = await userorm.get_one_by(username=data.username_or_email)
    if user is None or not verify_password(data.password, user.password):
        raise HTTPException(401, 'Invalid username or password')
    session_key = token_hex(16)
    await userorm.add_session_key(user.id, session_key)
    return pass_fields(LoginResponse, user, api_session_key=session_key)

@router.post('/logout')
async def logout(session_key: str = Depends(get_session_key),
                 userorm: UsersOrm = Depends(UsersOrm.get_orm)):
    user = await get_current_user(session_key, userorm)
    if session_key:
        await userorm.remove_session_key(user_id=user['_id'], session_key=session_key)
    return

@router.post('/update_password')
async def update_password(data: UpdatePasswordRequest,
                          session_key: str = Depends(get_session_key),
                          userorm: UsersOrm = Depends(UsersOrm.get_orm)):
    user = await get_current_user(session_key, userorm)
    if not verify_password(data.old_password, user.password):
        raise HTTPException(401, 'Invalid old password')
    await userorm.update_by_id(user['_id'], password=hash_password(data.new_password))
    return
