from fastapi import Depends, HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session
from auth import get_current_user
from models import User, Goal, UserGoal, AuthSession

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.user_role != "admin":
        raise HTTPException(status_code=403, detail="Нужны права администратора.")
    return user

def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    return user

def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.user_id)))

def set_banned(db: Session, admin: User, user_id: int, banned: bool) -> User:
    user = get_user_or_404(db, user_id)
    if user.user_id == admin.user_id:
        raise HTTPException(status_code=409, detail="Нельзя заблокировать самого себя.")
    user.banned = banned
    if banned:
        # Отзываем все сессии, чтобы по refresh-токену нельзя было получить новый access
        db.execute(update(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None)).values(revoked_at=func.now()))
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, admin: User, user_id: int):
    user = get_user_or_404(db, user_id)
    if user.user_id == admin.user_id:
        raise HTTPException(status_code=409, detail="Нельзя удалить самого себя.")
    # Цели, где пользователь владелец, удаляются вместе с задачами (README, раздел 5, пункт 6).
    # Все остальное (участие в чужих целях, назначения, сессии) удаляет база каскадно
    owned_goals = select(UserGoal.goal_id).where(UserGoal.user_id == user_id, UserGoal.goal_role == "owner")
    db.execute(delete(Goal).where(Goal.goal_id.in_(owned_goals)))
    db.execute(delete(User).where(User.user_id == user_id))
    db.commit()
