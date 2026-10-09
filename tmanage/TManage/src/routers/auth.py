"""
Эндпоинты регистрации, авторизации и аунтентификации.

Оганнисян Ваган
05.10.2026
"""
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import hash_password, verify_password, create_access_token
from models import User

#@app.get("/items/{item_id}")
#def read_item(item_id: int):
#    return {"item_id": item_id, "status": f"Товар {item_id} успешно найден"}
router: APIRouter = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/")
def read_root():
    return {"message": "Hello, world!"}

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

class UserLogin(BaseModel):
    login: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOutput(BaseModel):
    user_id: int
    login: str
    first_name: str
    last_name: str
    user_role: str

@router.post("/v1/register", response_model=TokenResponse, summary="Регистрация")
async def register(data: UserRegister, session: AsyncSession = Depends(get_db)):
    user = User(
        login=data.username,
        first_name=data.first_name,
        last_name=data.last_name,
        password_hash=hash_password(data.password),
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(user.user_id)
    return TokenResponse(access_token=token, token_type="bearer")

@router.post("/v1/login", response_model=TokenResponse, summary="Авторизация")
async def login(data: UserLogin,  session: AsyncSession = Depends(get_db)):
    res = await session.execute(select(User).where(User.login == data.login))

    user = res.scalar_one_or_none()

    if not user or not verify_password(user.password_hash, data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    if user.banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User banned")
    
    token = create_access_token(user.user_id)
    return TokenResponse(access_token=token, token_type="bearer")

@router.get("/v1/users")
def get_users(user_id: int):
    return {"user_id": user_id}

@router.get("/v1/goals")
def get_goals(goal_id: int):
    return {"goal_id": goal_id}

@router.get("/v1/tasks")
def get_tasks(task_id: int):
    return {"task_id": task_id}