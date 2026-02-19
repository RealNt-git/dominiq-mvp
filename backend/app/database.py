# backend/app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Чтение URL базы данных из переменной окружения или значение по умолчанию
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dominiq:dominiq@localhost:5432/dominiq")

# Для PostgreSQL не требуется специальных аргументов подключения
engine = create_engine(DATABASE_URL, poolclass=NullPool)
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