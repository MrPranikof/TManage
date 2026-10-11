"""
Эндпоинты регистрации, авторизации и аунтентификации.

Оганнисян Ваган
05.10.2026
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth import register_user, login_user, get_current_user
from core.database import get_db
from core.security import create_access_token
from models import User
from schemas import RegisterInput, LoginInput, UserOutput, TokenOutput

router = APIRouter(prefix="/v1/auth", tags=["auth"])

@router.post("/register", response_model=UserOutput, status_code=201, summary="Регистрация")
def register(data: RegisterInput, db: Session = Depends(get_db)):
    return register_user(db, data.login, data.first_name, data.last_name, data.password)

@router.post("/login", response_model=TokenOutput, summary="Авторизация")
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = login_user(db, data.login, data.password)
    return {"access_token": create_access_token(user.user_id)}

@router.get("/me", response_model=UserOutput, summary="Текущий пользователь")
def me(user: User = Depends(get_current_user)):
    return user
