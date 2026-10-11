from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from models import User, Goal, Task, UserGoal, UserTask
from statuses import CLOSED_STATUSES, apply_status

def get_goal_and_role(db: Session, goal_id: int, user: User) -> tuple[Goal, str]:
    """Возвращает цель и роль пользователя в ней. Если цели нет или пользователь в ней не состоит, бросает ошибку."""
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Цель не найдена.")
    role = db.scalar(select(UserGoal.goal_role).where(UserGoal.goal_id == goal_id, UserGoal.user_id == user.user_id))
    if role is None:
        raise HTTPException(status_code=403, detail="Вы не состоите в этой цели.")
    return goal, role

def require_role(role: str, allowed: tuple):
    if role not in allowed:
        raise HTTPException(status_code=403, detail="Недостаточно прав.")

def check_dates(start_date: datetime | None, deadline: datetime | None):
    if start_date is not None and deadline is not None and start_date > deadline:
        raise HTTPException(status_code=422, detail="Дата начала не может быть позже дедлайна.")

def goal_to_output(db: Session, goal: Goal, role: str) -> dict:
    # Прогресс: выполненные задачи / все задачи, кроме отмененных. Если задач нет, прогресс 0
    counts = dict(db.execute(select(Task.status, func.count()).where(Task.goal_id == goal.goal_id).group_by(Task.status)).all())
    tasks_done = counts.get("done", 0)
    tasks_total = sum(count for status, count in counts.items() if status != "cancelled")
    return {
        "goal_id": goal.goal_id, "name": goal.name, "description": goal.description, "status": goal.status,
        "start_date": goal.start_date, "deadline": goal.deadline, "completed_at": goal.completed_at,
        "created_at": goal.created_at, "updated_at": goal.updated_at,
        "my_role": role, "tasks_total": tasks_total, "tasks_done": tasks_done,
        "progress": round(tasks_done * 100 / tasks_total) if tasks_total else 0,
    }

def create_goal(db: Session, user: User, name: str, description: str | None, start_date: datetime | None, deadline: datetime | None) -> dict:
    check_dates(start_date, deadline)
    goal = Goal(name=name, description=description, start_date=start_date, deadline=deadline)
    db.add(goal)
    db.flush()
    db.add(UserGoal(user_id=user.user_id, goal_id=goal.goal_id, goal_role="owner"))
    db.commit()
    db.refresh(goal)
    return goal_to_output(db, goal, "owner")

def list_goals(db: Session, user: User) -> list[dict]:
    rows = db.execute(select(Goal, UserGoal.goal_role).join(UserGoal, UserGoal.goal_id == Goal.goal_id).where(UserGoal.user_id == user.user_id).order_by(Goal.goal_id)).all()
    return [goal_to_output(db, goal, role) for goal, role in rows]

def get_goal(db: Session, user: User, goal_id: int) -> dict:
    goal, role = get_goal_and_role(db, goal_id, user)
    return goal_to_output(db, goal, role)

def update_goal(db: Session, user: User, goal_id: int, changes: dict) -> dict:
    goal, role = get_goal_and_role(db, goal_id, user)
    require_role(role, ("owner", "moderator"))
    if "name" in changes and changes["name"] is None:
        raise HTTPException(status_code=422, detail="Название не может быть пустым.")
    for field, value in changes.items():
        setattr(goal, field, value)
    check_dates(goal.start_date, goal.deadline)
    if goal.deadline is not None:
        late_task = db.scalar(select(Task.task_id).where(Task.goal_id == goal_id, Task.deadline > goal.deadline).limit(1))
        if late_task is not None:
            raise HTTPException(status_code=409, detail="У цели есть задачи с более поздним дедлайном.")
    db.commit()
    db.refresh(goal)
    return goal_to_output(db, goal, role)

def change_goal_status(db: Session, user: User, goal_id: int, new_status: str) -> dict:
    goal, role = get_goal_and_role(db, goal_id, user)
    require_role(role, ("owner", "moderator"))
    if new_status == "done":
        open_task = db.scalar(select(Task.task_id).where(Task.goal_id == goal_id, Task.status.not_in(CLOSED_STATUSES)).limit(1))
        if open_task is not None:
            raise HTTPException(status_code=409, detail="Цель можно завершить, только когда все ее задачи выполнены или отменены.")
    apply_status(goal, new_status)
    db.commit()
    db.refresh(goal)
    return goal_to_output(db, goal, role)

def delete_goal(db: Session, user: User, goal_id: int):
    goal, role = get_goal_and_role(db, goal_id, user)
    require_role(role, ("owner",))
    # Задачи, назначения и участников удаляет база каскадно
    db.delete(goal)
    db.commit()

def list_members(db: Session, user: User, goal_id: int) -> list[dict]:
    get_goal_and_role(db, goal_id, user)
    rows = db.execute(select(User, UserGoal.goal_role).join(UserGoal, UserGoal.user_id == User.user_id).where(UserGoal.goal_id == goal_id).order_by(User.user_id)).all()
    return [{"user_id": member.user_id, "login": member.login, "first_name": member.first_name, "last_name": member.last_name, "goal_role": role} for member, role in rows]

def get_membership(db: Session, goal_id: int, member_id: int) -> UserGoal:
    membership = db.get(UserGoal, (member_id, goal_id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Пользователь не состоит в цели.")
    if membership.goal_role == "owner":
        raise HTTPException(status_code=409, detail="Владельца цели нельзя изменить или удалить.")
    return membership

def add_member(db: Session, user: User, goal_id: int, login: str) -> list[dict]:
    goal, role = get_goal_and_role(db, goal_id, user)
    require_role(role, ("owner",))
    member = db.scalar(select(User).where(User.login == login))
    if member is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    if db.get(UserGoal, (member.user_id, goal_id)) is not None:
        raise HTTPException(status_code=409, detail="Пользователь уже состоит в цели.")
    db.add(UserGoal(user_id=member.user_id, goal_id=goal_id, goal_role="member"))
    db.commit()
    return list_members(db, user, goal_id)

def set_member_role(db: Session, user: User, goal_id: int, member_id: int, goal_role: str) -> list[dict]:
    goal, role = get_goal_and_role(db, goal_id, user)
    require_role(role, ("owner",))
    membership = get_membership(db, goal_id, member_id)
    membership.goal_role = goal_role
    db.commit()
    return list_members(db, user, goal_id)

def remove_member(db: Session, user: User, goal_id: int, member_id: int):
    goal, role = get_goal_and_role(db, goal_id, user)
    require_role(role, ("owner",))
    membership = get_membership(db, goal_id, member_id)
    # Исполнителем может быть только участник цели, поэтому вместе с участием снимаем и назначения
    goal_tasks = select(Task.task_id).where(Task.goal_id == goal_id)
    db.execute(delete(UserTask).where(UserTask.user_id == member_id, UserTask.task_id.in_(goal_tasks)))
    db.delete(membership)
    db.commit()
