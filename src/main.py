from fastapi import FastAPI
from routers.auth import router as auth_router


#@app.get("/items/{item_id}")
#def read_item(item_id: int):
#    return {"item_id": item_id, "status": f"Товар {item_id} успешно найден"}
app = FastAPI(title="TManage API", version="1.0.0")
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Hello, world!"}

@app.get("/v1/users")
def get_users(user_id: int):
    return {"user_id": user_id}

@app.get("/v1/goals")
def get_goals(goal_id: int):
    return {"goal_id": goal_id}

@app.get("/v1/tasks")
def get_tasks(task_id: int):
    return {"task_id": task_id}