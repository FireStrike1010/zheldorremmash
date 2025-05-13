from fastapi import APIRouter, HTTPException, Depends
from secrets import token_hex
from database import User
from models.auth import LoginRequest, LoginResponse, UpdatePasswordRequest
from utils.email_validator import is_email
from utils.password_hasher import verify_password, hash_password
from utils.session_validator import get_current_user, get_session_key


router = APIRouter(prefix='/auth', tags=['Auth'])

@router.post('/login', response_model=LoginResponse)
async def login(data: LoginRequest):
    try:
        if is_email(data.username_or_email):
            user = await User.get_one_by_email(data.username_or_email)
        else:
            user = await User.get_one_by_username(data.username_or_email)
    except ValueError:
        raise HTTPException(401, 'Invalid username/email or password')
    if not verify_password(data.password, user.password):
        raise HTTPException(401, 'Invalid username/email or password')
    session_key = token_hex(16)
    await user.register_new_session_key(session_key)
    return LoginResponse.model_validate(user)

@router.post('/logout')
async def logout(session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    await user.unregister_session_key()

@router.post('/update_password')
async def update_password(data: UpdatePasswordRequest, session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    if not verify_password(data.old_password, user.password):
        raise HTTPException(401, 'Invalid old password')
    await user.update_params(password=hash_password(data.new_password))