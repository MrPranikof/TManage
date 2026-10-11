"""
Функции регистрации, авторизации и аунтентификации.

Оганнисян Ваган
05.10.2026
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import hash_password, verify_password, decode_access_token
from models import User

bearer = HTTPBearer(auto_error=False)

def register_user(db: Session, login: str, first_name: str, last_name: str, password: str) -> User:
    if db.scalar(select(User).where(User.login == login)) is not None:
        raise HTTPException(status_code=409, detail="Логин уже существует.")
    user = User(login=login, first_name=first_name, last_name=last_name, password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Два одновременных запроса с одним логином: второй упирается в UNIQUE в базе
        db.rollback()
        raise HTTPException(status_code=409, detail="Логин уже существует.")
    db.refresh(user)
    return user

def login_user(db: Session, login: str, password: str) -> User:
    user = db.scalar(select(User).where(User.login == login))
    if user is None or not verify_password(user.password_hash, password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль.")
    # Бан проверяем после пароля, чтобы не раскрывать его тому, кто пароля не знает
    if user.banned:
        raise HTTPException(status_code=403, detail="Пользователь заблокирован.")
    return user

def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Нет токена.", headers={"WWW-Authenticate": "Bearer"})
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Токен недействителен.", headers={"WWW-Authenticate": "Bearer"})
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Токен недействителен.", headers={"WWW-Authenticate": "Bearer"})
    if user.banned:
        raise HTTPException(status_code=403, detail="Пользователь заблокирован.")
    return user
