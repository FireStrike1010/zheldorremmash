from typing import Optional, Self, Literal, List, NoReturn, Dict, Any
from pydantic import EmailStr, Base64Bytes
from beanie import Document, Indexed
from datetime import datetime, timedelta
from models.users import AddUserRequest
from utils.password_hasher import hash_password


Roles = Literal['Admin', 'Moderator', 'Auditor', 'User']

class User(Document):
    username: Indexed(str, unique=True) # type: ignore
    email: Indexed(EmailStr, unique=True) # type: ignore
    telegram: Optional[str] = None
    photo: Optional[Base64Bytes] = None
    name: str
    surname: str
    patronymic: Optional[str] = None
    job_title: Optional[str] = None
    role: Roles = 'User'
    created_at: datetime
    last_login: Optional[datetime] = None
    password: str
    api_session_key: Optional[Indexed(str, index_type='text')] = None # type: ignore

    class Settings:
        name = "Users"
        use_cache = False
        use_state_management = True
        cache_expiration_time = timedelta(hours=1)
    
    @classmethod
    async def add_one(cls, user: AddUserRequest) -> Self | NoReturn:
        user.password = hash_password(user.password)
        new_user = cls(**user.model_dump(), created_at=datetime.now())
        return await new_user.insert()
    
    @classmethod
    async def get_all(cls) -> List[Self]:
        return await cls.find_all().to_list()
    
    @classmethod
    async def get_one_by_username(cls, username: str) -> Self | NoReturn:
        user = await cls.find_one(cls.username==username)
        if not user:
            raise ValueError(f'User with username {username} not found')
        return user
    
    @classmethod
    async def get_one_by_email(cls, email: EmailStr | str) -> Self | NoReturn:
        user = await cls.find_one(cls.email==email)
        if not user:
            raise ValueError(f'User with email {email} not found')
        return user
    
    async def register_new_session_key(self, session_key: str) -> None:
        self.last_login = datetime.now()
        self.api_session_key = session_key
        await self.save_changes()

    async def unregister_session_key(self) -> None:
        self.api_session_key = None
        await self.save_changes()
    
    async def update_params(self, **kwargs) -> None | NoReturn:
        await self.set(kwargs)
        await self.save_changes()

    @classmethod
    async def update_by_username(cls, username: str, new_data: Dict[str, Any]) -> Self | NoReturn:
        user = await cls.find_one(cls.username == username)
        if not user:
            raise ValueError(f'User with username {username} not found')
        await user.update_params(**new_data)
        return user
    
    @classmethod
    async def get_one_by_session_key(cls, session_key: str) -> Self | NoReturn:
        user = await cls.find_one(cls.api_session_key==session_key)
        if not user:
            raise ValueError(f"User with session key {session_key} not found")
        return user

    @classmethod
    async def validate_access(cls, session_key: str) -> Roles | NoReturn:
        result = await cls.find_one(cls.api_session_key==session_key)
        if not result:
            raise ValueError(f"User with session key {session_key} not found")
        return result.role