from core.config import SECRET_JWT, ALGORITHM, ACCESS_TOKEN_MINUTES
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    try:
        ph.verify(password_hash, password)
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False

def create_access_token(user_id: int)  -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "typ": "access"
    }
    return jwt.encode(payload, SECRET_JWT, algorithm=ALGORITHM)

def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_JWT, algorithms=[ALGORITHM])

        if payload.get("typ") != "access":
            return None

        sub = payload.get("sub")
        if sub is None:
            return None

        return int(sub)

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except ValueError:
        # Если sub вдруг не число, int() кинет valueError
        return None

def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    # В базе хранится только хеш refresh-токена. Токен случайный и длинный, поэтому хватает sha256
    return hashlib.sha256(token.encode()).hexdigest()
