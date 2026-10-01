from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


#@app.get("/items/{item_id}")
#def read_item(item_id: int):
#    return {"item_id": item_id, "status": f"Товар {item_id} успешно найден"}
app = FastAPI(title="TManage API", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "Hello, world!"}


class UserInput(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)

class UserOutput(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool

@app.post("/v1/auth/register", response_model=UserOutput, summary="Регистрация")
def register(data: UserInput):
    pass


@app.post("/v1/auth/login", response_model=UserOutput, summary="Регистрация")
def login(data: UserInput):
    pass

@app.get("/v1/users")
def get_users(user_id: int):
    return {"user_id": user_id}

@app.get("/v1/goals")
def get_goals(goal_id: int):
    return {"goal_id": goal_id}

@app.get("/v1/tasks")
def get_tasks(task_id: int):
    return {"task_id": task_id}