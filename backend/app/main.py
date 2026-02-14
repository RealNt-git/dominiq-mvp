# backend/app/main.py
# Главный файл FastAPI приложения
# Добавлен глобальный обработчик необработанных исключений

import logging
import sys
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, init_db, SessionLocal
from app import models
from app.api import auth, content, learning, gamification, ai_assistant
from app.utils.helpers import ensure_default_domains

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальный обработчик необработанных исключений
def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = global_exception_handler

# Создание таблиц БД при запуске
init_db()

# Создание стандартных доменов
db = SessionLocal()
try:
    ensure_default_domains(db)
finally:
    db.close()

app = FastAPI(title="Dominiq MVP", version="1.0.0")

# Настройка CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth")
app.include_router(content.content_router, prefix="/api")
app.include_router(learning.router, prefix="/api/learn")
app.include_router(gamification.router, prefix="/api/user")
app.include_router(ai_assistant.router, prefix="/api/admin/ai")

@app.get("/")
def root():
    return {"message": "Dominiq API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}