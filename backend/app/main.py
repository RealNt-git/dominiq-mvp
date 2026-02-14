# backend/app/main.py
# Главный файл FastAPI приложения

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, init_db
from app import models
from app.api import auth, content, learning, gamification, ai_assistant

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц БД при запуске
init_db()

app = FastAPI(title="Dominiq MVP", version="1.0.0")

# Настройка CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # адрес фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth")
app.include_router(content.content_router, prefix="/api")  # в content.py определён content_router
app.include_router(learning.router, prefix="/api/learn")
app.include_router(gamification.router, prefix="/api/user")
app.include_router(ai_assistant.router, prefix="/api/admin/ai")

@app.get("/")
def root():
    return {"message": "Dominiq API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}