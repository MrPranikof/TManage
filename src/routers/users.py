from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models import User
from schemas import BanInput, UserOutput
from users import require_admin, list_users, set_banned, delete_user

router = APIRouter(prefix="/v1/users", tags=["users (admin)"])

@router.get("", response_model=list[UserOutput], summary="Список пользователей")
def read_all(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return list_users(db)

@router.patch("/{user_id}/ban", response_model=UserOutput, summary="Блокировка и разблокировка пользователя")
def ban(user_id: int, data: BanInput, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return set_banned(db, admin, user_id, data.banned)

@router.delete("/{user_id}", status_code=204, summary="Удаление пользователя")
def remove(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    delete_user(db, admin, user_id)
