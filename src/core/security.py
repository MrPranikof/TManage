"""
Функции хэширования пароля и создания access-токенов

Оганнисян Ваган
05.10.2026
"""

from core.config import SECRET_JWT, ALGORITHM, ACCESS_TOKEN_MINUTES
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
from datetime import datetime, timedelta, timezone

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    try:
        ph.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False

def create_access_token(login: str):
    payload = {"sub": login, "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)}
    return jwt.encode(payload, SECRET_JWT, algorithm=ALGORITHM)

def decode_access_token(token):
    try:
        payload = jwt.decode(token, SECRET_JWT, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None