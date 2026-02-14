# backend/app/database.py
# Модуль настройки подключения к базе данных SQLite
# Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Чтение URL базы данных из переменной окружения или значение по умолчанию
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dominiq.db")

# Для SQLite требуется отключать проверку использования в нескольких потоках
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Зависимость FastAPI для получения сессии базы данных.
    Сессия автоматически закрывается после завершения запроса.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Создаёт все таблицы в базе данных, определённые в моделях.
    Вызывается при старте приложения (в main.py).
    """
    Base.metadata.create_all(bind=engine)
