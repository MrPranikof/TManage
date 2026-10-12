from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth import get_current_user
from core.database import get_db
from models import User
from schemas import TaskCreate, TaskUpdate, TaskOutput, StatusInput, AssigneesInput
from tasks import list_tasks, create_task, get_task, update_task, change_task_status, set_assignees, delete_task

router = APIRouter(prefix="/v1", tags=["tasks"])

@router.get("/goals/{goal_id}/tasks", response_model=list[TaskOutput], summary="Задачи цели")
def read_all(goal_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_tasks(db, user, goal_id)

@router.post("/goals/{goal_id}/tasks", response_model=TaskOutput, status_code=201, summary="Создание задачи")
def create(goal_id: int, data: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_task(db, user, goal_id, data.name, data.description, data.start_date, data.deadline, data.assignee_ids)

@router.get("/tasks/{task_id}", response_model=TaskOutput, summary="Одна задача")
def read(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_task(db, user, task_id)

@router.patch("/tasks/{task_id}", response_model=TaskOutput, summary="Изменение задачи")
def update(task_id: int, data: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return update_task(db, user, task_id, data.model_dump(exclude_unset=True))

@router.patch("/tasks/{task_id}/status", response_model=TaskOutput, summary="Изменение статуса задачи")
def set_status(task_id: int, data: StatusInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return change_task_status(db, user, task_id, data.status)

@router.put("/tasks/{task_id}/assignees", response_model=TaskOutput, summary="Назначение исполнителей")
def update_assignees(task_id: int, data: AssigneesInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return set_assignees(db, user, task_id, data.user_ids)

@router.delete("/tasks/{task_id}", status_code=204, summary="Удаление задачи")
def remove(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    delete_task(db, user, task_id)
