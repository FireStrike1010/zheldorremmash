from pydantic import BaseModel, Field, EmailStr, Base64Bytes
from datetime import datetime
from typing import Optional, Literal, List


class AddUserRequest(BaseModel):
    username: str = Field(description='Username')
    email: EmailStr = Field(description='Email')
    telegram: Optional[str] = Field(default=None, description='Telegram profile (@example)')
    photo: Optional[Base64Bytes] = Field(default=None, description='Photo (avatar) in base64 format')
    name: str = Field(description='First name')
    surname: str = Field(description='Second name')
    patronymic: Optional[str] = Field(default=None, description='Patronymic')
    role: Literal['Admin', 'Moderator', 'Auditor', 'User'] = Field(default='User', description='Roles with different access levels')
    job_title: Optional[str] = Field(default=None, description='Job title')
    password: str = Field(description='Password')

class AddUserResponse(BaseModel):
    id: str = Field(alias="_id", description='ID of user in mongodb')
    created_at: datetime = Field(description='Date and time of creation')

class UpdateUserRequest(BaseModel):
    username: Optional[str] = Field(default=None, description='Username (can be changed by admin only)')
    email: Optional[EmailStr] = Field(default=None, description='Email (can be changed by admin only)')
    telegram: Optional[str] = Field(default=None, description='Telegram profile (@example)')
    photo: Optional[bytes] = Field(default=None, description='Photo (avatar) in base64 format')
    name: Optional[str] = Field(default=None, description='First name')
    surname: Optional[str] = Field(default=None, description='Second name')
    patronymic: Optional[str] = Field(default=None, description='Patronymic')
    role: Optional[Literal['Admin', 'Moderator', 'Auditor', 'User']] = Field(default=None, description='Roles with different access levels (can be changed by admin only)')
    job_title: Optional[str] = Field(default=None, description='Job title (can be changed by admin only)')
    password: Optional[str] = Field(default=None, description='Password (can be changed by admin only)')

class User(BaseModel):
    username: str = Field(description='Username')
    email: EmailStr = Field(description='Email')
    telegram: Optional[str] = Field(default=None, description='Telegram profile (@example)')
    photo: Optional[bytes] = Field(default=None, description='Photo (avatar) in base64 format')
    name: str = Field(description='First name')
    surname: str = Field(description='Second name')
    patronymic: Optional[str] = Field(default=None, description='Patronymic')
    role: Literal['Admin', 'Moderator', 'Auditor', 'User'] = Field(default='User', description='Roles with different access levels')
    job_title: Optional[str] = Field(default=None, description='Job title')

class DeleteManyRequest(BaseModel):
    usernames: List[str] = Field(description='List of usernames to delete')