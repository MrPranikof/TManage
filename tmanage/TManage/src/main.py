"""
Точка входа приложения TManage
Оганнисян Ваган
05.10.2026
"""
from fastapi import FastAPI

from routers import auth

app = FastAPI(title="TManage API", version="1.0.0")


app.include_router(auth.router, prefix="/v1")


@app.get("/")
def read_root():
    return {"message": "Hello, world!"}