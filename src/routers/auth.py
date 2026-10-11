from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth import register_user, login_user, get_current_user, create_session, refresh_session, logout_session
from core.database import get_db
from models import User
from schemas import RegisterInput, LoginInput, RefreshInput, UserOutput, TokenOutput

router = APIRouter(prefix="/v1/auth", tags=["auth"])

@router.post("/register", response_model=UserOutput, status_code=201, summary="Регистрация")
def register(data: RegisterInput, db: Session = Depends(get_db)):
    return register_user(db, data.login, data.first_name, data.last_name, data.password)

@router.post("/login", response_model=TokenOutput, summary="Авторизация")
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = login_user(db, data.login, data.password)
    access_token, refresh_token = create_session(db, user)
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post("/refresh", response_model=TokenOutput, summary="Обновление токенов")
def refresh(data: RefreshInput, db: Session = Depends(get_db)):
    access_token, refresh_token = refresh_session(db, data.refresh_token)
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post("/logout", status_code=204, summary="Выход")
def logout(data: RefreshInput, db: Session = Depends(get_db)):
    logout_session(db, data.refresh_token)

@router.get("/me", response_model=UserOutput, summary="Текущий пользователь")
def me(user: User = Depends(get_current_user)):
    return user
