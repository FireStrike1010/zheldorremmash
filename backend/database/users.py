from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError
from typing import Optional, Self, Literal, List, NoReturn, Dict, Any
from utils.pydantic_utils import PyObjectId
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


class UserSchema(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    id: Optional[PyObjectId] = Field(default=None, alias='_id')
    username: str
    email: EmailStr
    telegram: Optional[str] = None
    photo: Optional[bytes] = None
    name: str
    surname: str
    patronymic: Optional[str] = None
    job_title: Optional[str] = None
    role: Literal['Admin', 'Moderator', 'Auditor', 'User'] = 'User'
    created_at: datetime
    last_login: Optional[datetime] = None
    password: str
    session_keys: List[str] = Field(default_factory=list)


class UsersOrm:
    @staticmethod
    def get_orm(request: Request) -> Self:
        return UsersOrm(request.app.state.db['Users'], request.app.state.config.get('MASTER_KEY'))

    def __init__(self, collection_instance: AsyncIOMotorCollection, master_key: Optional[str] = None) -> None:
        self._master_key = master_key
        self.collection = collection_instance
    
    async def add_one(self, user: UserSchema) -> UserSchema | NoReturn:
        if await self.collection.find_one({'email': user.email}):
            raise DuplicateKeyError(f'Email {user.email} is taken')
        if await self.collection.find_one({'username': user.username}):
            raise DuplicateKeyError(f'Username {user.username} is taken')
        orm_response = await self.collection.insert_one(user.model_dump(exclude={'id'}), True)
        user = await self.get_one_by(_id=orm_response.inserted_id)
        return user

    async def get_all(self) -> List[UserSchema]:
        users = await self.collection.find({}).to_list()
        return [UserSchema(**user) for user in users]
    
    async def get_many_by(self, **kwargs) -> List[UserSchema]:
        users = await self.collection.find(kwargs).to_list()
        return [UserSchema(**user) for user in users]

    async def get_one_by(self, **kwargs) -> Optional[UserSchema]:
        user = await self.collection.find_one(kwargs)
        return UserSchema(**user) if user else None
    
    async def add_session_key(self, user_id: str, new_session_key: str) -> None | NoReturn:
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {
                "$push": {"session_keys": new_session_key},
                "$set": {"last_login": datetime.now()}
            },
            return_document=False
        )
        if not result:
            raise ValueError(f'User with ID {user_id} not found')

    async def remove_session_key(self, user_id: str, session_key: str) -> None | NoReturn:
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$pull": {"session_keys": session_key}},
            return_document=False
        )
        if not result:
            raise ValueError(f'User with ID {user_id} not found or session key does not exist')

    async def update_by_id(self, user_id: str, kwargs: Dict[str, Any]) -> UserSchema | NoReturn:
        result = await self.collection.find_one_and_update(
            {'_id': ObjectId(user_id)},
            {'$set': kwargs},
            return_document=True
        )
        if not result:
            raise ValueError(f'User with ID {user_id} not found')
        return UserSchema(**result)
    
    async def update_by_username(self, username: str, kwargs: Dict[str, Any]) -> UserSchema | NoReturn:
        result = await self.collection.find_one_and_update(
            {'username': username},
            {'$set': kwargs},
            return_document=True
        )
        if not result:
            raise ValueError(f'User with username {username} not found')
        return UserSchema(**result)

    async def delete_by_username(self, username: str) -> None | NoReturn:
        result = await self.collection.find_one_and_delete({'username': username})
        if not result:
            raise ValueError(f'User with username {username} not found')

    async def validate_session_key(self, session_key: str) -> Dict[str, str] | NoReturn:
        if self._master_key and session_key == self._master_key:
            return {'role': 'Admin', 'username': 'Master'}
        user = await self.collection.find_one({'session_keys': {'$in': [session_key]}})
        if not user:
            raise ValueError('Invalid session key')
        return user