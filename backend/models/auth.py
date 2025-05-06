from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from database.users import Roles


class LoginRequest(BaseModel):
    username_or_email: str = Field(description='Username or email')
    password: str = Field(description='Password')

class LoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str = Field(description='Username')
    photo: Optional[bytes] = Field(default=None, description='Photo (avatar)')
    name: str = Field(description='First name')
    surname: str = Field(description='Second name')
    patronymic: Optional[str] = Field(default=None, description='Patronymic')
    role: Roles = Field(default='User', description='Roles with different access levels')
    api_session_key: str = Field(description='''Session key required for any other requests, 
                                 pass this value in headers as "session_key"''')

class UpdatePasswordRequest(BaseModel):
    old_password: str = Field(description='Old password')
    new_password: str = Field(description='New password')