from fastapi import FastAPI
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.goals import router as goals_router
from routers.tasks import router as tasks_router

app = FastAPI(title="TManage API", version="1.0.0")
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(goals_router)
app.include_router(tasks_router)

@app.get("/")
def read_root():
    return {"message": "Hello, world!"}