# backend/app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Чтение URL базы данных из переменной окружения или значение по умолчанию
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/dominiq.db")

# Для SQLite требуется отключать проверку использования в нескольких потоках
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Создаём директорию для базы данных, если её нет
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args=connect_args)
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