from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session
from goals import get_goal_and_role, require_role, check_dates
from models import User, Goal, Task, UserGoal, UserTask
from statuses import CLOSED_STATUSES, apply_status

def get_assignee_ids(db: Session, task_id: int) -> list[int]:
    return list(db.scalars(select(UserTask.user_id).where(UserTask.task_id == task_id).order_by(UserTask.user_id)))

def task_to_output(db: Session, task: Task) -> dict:
    return {
        "task_id": task.task_id, "goal_id": task.goal_id, "author_id": task.author_id,
        "name": task.name, "description": task.description, "status": task.status,
        "start_date": task.start_date, "deadline": task.deadline, "completed_at": task.completed_at,
        "created_at": task.created_at, "updated_at": task.updated_at,
        "assignee_ids": get_assignee_ids(db, task.task_id),
    }

def get_task_goal_role(db: Session, user: User, task_id: int) -> tuple[Task, Goal, str]:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена.")
    goal, role = get_goal_and_role(db, task.goal_id, user)
    return task, goal, role

def require_task_rights(db: Session, user: User, task: Task, role: str, assignee_allowed: bool = False):
    """Владелец и модератор цели и автор задачи могут все. Исполнитель - только то, где assignee_allowed."""
    if role in ("owner", "moderator") or task.author_id == user.user_id:
        return
    if assignee_allowed and user.user_id in get_assignee_ids(db, task.task_id):
        return
    raise HTTPException(status_code=403, detail="Недостаточно прав.")

def check_task_deadline(goal: Goal, deadline: datetime | None):
    if deadline is not None and goal.deadline is not None and deadline > goal.deadline:
        raise HTTPException(status_code=422, detail="Дедлайн задачи не может быть позже дедлайна цели.")

def check_assignees(db: Session, goal_id: int, user_ids: set[int]):
    members = set(db.scalars(select(UserGoal.user_id).where(UserGoal.goal_id == goal_id, UserGoal.user_id.in_(user_ids))))
    not_members = sorted(user_ids - members)
    if not_members:
        raise HTTPException(status_code=422, detail=f"Исполнителем можно назначить только участника цели. Не участники: {not_members}.")

def list_tasks(db: Session, user: User, goal_id: int) -> list[dict]:
    goal, role = get_goal_and_role(db, goal_id, user)
    query = select(Task).where(Task.goal_id == goal_id).order_by(Task.task_id)
    if role == "member":
        # Участник видит только задачи, где он исполнитель (и те, что создал сам, пока был модератором)
        my_tasks = select(UserTask.task_id).where(UserTask.user_id == user.user_id)
        query = query.where(or_(Task.task_id.in_(my_tasks), Task.author_id == user.user_id))
    return [task_to_output(db, task) for task in db.scalars(query)]

def create_task(db: Session, user: User, goal_id: int, name: str, description: str | None, start_date: datetime | None, deadline: datetime | None, assignee_ids: list[int]) -> dict:
    goal, role = get_goal_and_role(db, goal_id, user)
    require_role(role, ("owner", "moderator"))
    if goal.status in CLOSED_STATUSES:
        raise HTTPException(status_code=409, detail="Нельзя добавить задачу в закрытую цель.")
    check_dates(start_date, deadline)
    check_task_deadline(goal, deadline)
    check_assignees(db, goal_id, set(assignee_ids))
    task = Task(goal_id=goal_id, author_id=user.user_id, name=name, description=description, start_date=start_date, deadline=deadline)
    db.add(task)
    db.flush()
    for user_id in set(assignee_ids):
        db.add(UserTask(user_id=user_id, task_id=task.task_id))
    db.commit()
    db.refresh(task)
    return task_to_output(db, task)

def get_task(db: Session, user: User, task_id: int) -> dict:
    task, goal, role = get_task_goal_role(db, user, task_id)
    require_task_rights(db, user, task, role, assignee_allowed=True)
    return task_to_output(db, task)

def update_task(db: Session, user: User, task_id: int, changes: dict) -> dict:
    task, goal, role = get_task_goal_role(db, user, task_id)
    require_task_rights(db, user, task, role)
    if "name" in changes and changes["name"] is None:
        raise HTTPException(status_code=422, detail="Название не может быть пустым.")
    for field, value in changes.items():
        setattr(task, field, value)
    check_dates(task.start_date, task.deadline)
    check_task_deadline(goal, task.deadline)
    db.commit()
    db.refresh(task)
    return task_to_output(db, task)

def change_task_status(db: Session, user: User, task_id: int, new_status: str) -> dict:
    task, goal, role = get_task_goal_role(db, user, task_id)
    require_task_rights(db, user, task, role, assignee_allowed=True)
    if goal.status in CLOSED_STATUSES:
        # Иначе в завершенной цели появится незавершенная задача
        raise HTTPException(status_code=409, detail="Цель закрыта. Чтобы менять статусы задач, сначала переоткройте цель.")
    apply_status(task, new_status)
    db.commit()
    db.refresh(task)
    return task_to_output(db, task)

def set_assignees(db: Session, user: User, task_id: int, user_ids: list[int]) -> dict:
    task, goal, role = get_task_goal_role(db, user, task_id)
    require_task_rights(db, user, task, role)
    check_assignees(db, goal.goal_id, set(user_ids))
    db.execute(delete(UserTask).where(UserTask.task_id == task_id))
    for user_id in set(user_ids):
        db.add(UserTask(user_id=user_id, task_id=task_id))
    db.commit()
    return task_to_output(db, task)

def delete_task(db: Session, user: User, task_id: int):
    task, goal, role = get_task_goal_role(db, user, task_id)
    require_task_rights(db, user, task, role)
    db.delete(task)
    db.commit()
