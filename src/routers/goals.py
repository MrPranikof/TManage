from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth import get_current_user
from core.database import get_db
from goals import create_goal, list_goals, get_goal, update_goal, change_goal_status, delete_goal, list_members, add_member, set_member_role, remove_member
from models import User
from schemas import GoalCreate, GoalUpdate, GoalOutput, StatusInput, MemberAdd, MemberRoleInput, MemberOutput

router = APIRouter(prefix="/v1/goals", tags=["goals"])

@router.post("", response_model=GoalOutput, status_code=201, summary="Создание цели")
def create(data: GoalCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_goal(db, user, data.name, data.description, data.start_date, data.deadline)

@router.get("", response_model=list[GoalOutput], summary="Мои цели с прогрессом")
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_goals(db, user)

@router.get("/{goal_id}", response_model=GoalOutput, summary="Одна цель")
def read(goal_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_goal(db, user, goal_id)

@router.patch("/{goal_id}", response_model=GoalOutput, summary="Изменение цели")
def update(goal_id: int, data: GoalUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # exclude_unset: меняем только те поля, которые клиент прислал
    return update_goal(db, user, goal_id, data.model_dump(exclude_unset=True))

@router.patch("/{goal_id}/status", response_model=GoalOutput, summary="Изменение статуса цели")
def set_status(goal_id: int, data: StatusInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return change_goal_status(db, user, goal_id, data.status)

@router.delete("/{goal_id}", status_code=204, summary="Удаление цели")
def remove(goal_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    delete_goal(db, user, goal_id)

@router.get("/{goal_id}/members", response_model=list[MemberOutput], summary="Участники цели")
def read_members(goal_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_members(db, user, goal_id)

@router.post("/{goal_id}/members", response_model=list[MemberOutput], status_code=201, summary="Добавление участника в цель")
def create_member(goal_id: int, data: MemberAdd, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return add_member(db, user, goal_id, data.login)

@router.patch("/{goal_id}/members/{user_id}", response_model=list[MemberOutput], summary="Назначение и снятие модератора")
def update_member(goal_id: int, user_id: int, data: MemberRoleInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return set_member_role(db, user, goal_id, user_id, data.goal_role)

@router.delete("/{goal_id}/members/{user_id}", status_code=204, summary="Удаление участника из цели")
def delete_member(goal_id: int, user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    remove_member(db, user, goal_id, user_id)
