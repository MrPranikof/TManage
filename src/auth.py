from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from core.config import REFRESH_TOKEN_DAYS
from core.database import get_db
from core.security import hash_password, verify_password, create_access_token, decode_access_token, create_refresh_token, hash_token
from models import User, AuthSession, RefreshToken

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

def add_refresh_token(db: Session, session_id: int) -> str:
    token = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)
    db.add(RefreshToken(session_id=session_id, token_hash=hash_token(token), expires_at=expires_at))
    return token

def create_session(db: Session, user: User) -> tuple[str, str]:
    """Создает сессию (один вход) и возвращает пару: access-токен и refresh-токен."""
    session = AuthSession(user_id=user.user_id)
    db.add(session)
    db.flush()
    refresh_token = add_refresh_token(db, session.session_id)
    db.commit()
    return create_access_token(user.user_id), refresh_token

def refresh_session(db: Session, refresh_token: str) -> tuple[str, str]:
    """Меняет refresh-токен на новую пару токенов. Старый токен после этого не действует."""
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
    if record is None:
        raise HTTPException(status_code=401, detail="Refresh-токен недействителен.")
    session = db.get(AuthSession, record.session_id)
    if session.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Сессия отозвана.")
    if record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh-токен истек.")

    # Помечаем токен использованным одним запросом: из двух одновременных refresh пройдет только один
    marked = db.execute(update(RefreshToken).where(RefreshToken.token_id == record.token_id, RefreshToken.used_at.is_(None)).values(used_at=func.now()))
    if marked.rowcount == 0:
        # Одноразовый токен пришел второй раз, значит его украли: отзываем всю сессию
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh-токен уже использован, сессия отозвана.")

    user = db.get(User, session.user_id)
    if user.banned:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=403, detail="Пользователь заблокирован.")

    new_refresh_token = add_refresh_token(db, session.session_id)
    db.commit()
    return create_access_token(user.user_id), new_refresh_token

def logout_session(db: Session, refresh_token: str):
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
    if record is None:
        return
    session = db.get(AuthSession, record.session_id)
    if session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
