from datetime import datetime
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

Status = Literal["new", "in_progress", "done", "cancelled"]

# --- Пользователи и аутентификация ---

class RegisterInput(BaseModel):
    login: str = Field(..., min_length=1, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)

class LoginInput(BaseModel):
    login: str
    password: str

class RefreshInput(BaseModel):
    refresh_token: str

class UserOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    login: str
    first_name: str
    last_name: str
    user_role: str
    banned: bool
    created_at: datetime

class TokenOutput(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class BanInput(BaseModel):
    banned: bool

# --- Цели ---

class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    start_date: AwareDatetime | None = None
    deadline: AwareDatetime | None = None

class GoalUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    start_date: AwareDatetime | None = None
    deadline: AwareDatetime | None = None

class StatusInput(BaseModel):
    status: Status

class GoalOutput(BaseModel):
    goal_id: int
    name: str
    description: str | None
    status: Status
    start_date: datetime | None
    deadline: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    my_role: Literal["owner", "moderator", "member"]
    tasks_total: int
    tasks_done: int
    progress: int

# --- Участники цели ---

class MemberAdd(BaseModel):
    login: str

class MemberRoleInput(BaseModel):
    goal_role: Literal["moderator", "member"]

class MemberOutput(BaseModel):
    user_id: int
    login: str
    first_name: str
    last_name: str
    goal_role: Literal["owner", "moderator", "member"]

# --- Задачи ---

class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    start_date: AwareDatetime | None = None
    deadline: AwareDatetime | None = None
    assignee_ids: list[int] = []

class TaskUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    start_date: AwareDatetime | None = None
    deadline: AwareDatetime | None = None

class AssigneesInput(BaseModel):
    user_ids: list[int]

class TaskOutput(BaseModel):
    task_id: int
    goal_id: int
    author_id: int | None
    name: str
    description: str | None
    status: Status
    start_date: datetime | None
    deadline: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    assignee_ids: list[int]
