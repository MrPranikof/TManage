"""
Конфиг

Оганнисян Ваган
05.10.2026
"""
import os
from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()

SECRET_JWT = os.getenv('SECRET_JWT')
ACCESS_TOKEN_MINUTES = int(os.getenv('ACCESS_TOKEN_MINUTES', 15))
ALGORITHM = os.getenv('ALGORITHM')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

DATABASE_URL = URL.create(
"postgresql+psycopg",
    host=DB_HOST,
    port=int(DB_PORT),
    username=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
)