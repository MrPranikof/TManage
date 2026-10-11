"""
Схемы запросов и ответов.

Оганнисян Ваган
11.10.2026
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class RegisterInput(BaseModel):
    login: str = Field(..., min_length=1, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)

class LoginInput(BaseModel):
    login: str
    password: str

class UserOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    login: str
    first_name: str
    last_name: str
    user_role: str
    banned: bool
    created_at: datetime

class TokenOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
