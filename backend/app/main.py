# backend/app/main.py
# Главный файл FastAPI приложения
# Добавлен глобальный обработчик необработанных исключений
# Добавлены метрики Prometheus и логирование в Logstash

import logging
import sys
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, init_db, SessionLocal
from app import models
from app.api import auth, content, learning, gamification, ai_assistant, plan  # добавлен plan
from app.utils.helpers import ensure_default_domains, ensure_default_grades  # добавлен ensure_default_grades

# Импорты для Prometheus и Logstash
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge
import logstash

# Импорт кастомных метрик из отдельного модуля (для предотвращения циклических импортов)
from app.core.metrics import (
    document_upload_total,
    document_processing_duration_seconds,
    active_users,
    http_request_duration_seconds
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Добавляем отправку логов в Logstash
try:
    logstash_handler = logstash.TCPLogstashHandler('logstash', 5000, version=1)
    # Добавляем к корневому логгеру (чтобы все логи приложения шли в Logstash)
    logging.getLogger().addHandler(logstash_handler)
    logger.info("Logstash handler added successfully")
except Exception as e:
    logger.error(f"Failed to connect to Logstash: {e}")

# Глобальный обработчик необработанных исключений
def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = global_exception_handler

# Создание таблиц БД при запуске
init_db()

# Создание стандартных доменов и грейдов
db = SessionLocal()
try:
    ensure_default_domains(db)
    ensure_default_grades(db)   # вызов новой функции
finally:
    db.close()

# Создаём приложение FastAPI
app = FastAPI(title="Dominiq MVP", version="1.0.0")

# === Инициализация метрик Prometheus ===
# Инструментатор для автоматического сбора метрик HTTP-запросов
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health"],
)
instrumentator.instrument(app).expose(app)

# === Настройка CORS ===
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
app.include_router(plan.router, prefix="/api/plan")  # подключили новый роутер

@app.get("/")
def root():
    return {"message": "Dominiq API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}