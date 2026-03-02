# backend/app/api/admin_reset.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

from app.database import get_db
from app.api.auth import get_current_user
from app import models
from app import schemas
from app.utils.helpers import ensure_default_domains, ensure_default_grades  # добавлено
from app.core.init_achievements import init_achievements  # добавлено

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

# Список таблиц в порядке удаления (сначала зависимые)
# Исправлено: user_progress перемещён выше terms
TABLES_IN_ORDER = [
    "draft_quizzes",          # зависит от documents
    "draft_terms",             # зависит от documents
    "documents",               # зависит от topics
    "processing_progress",     # зависит от documents
    "questions",               # зависит от quizzes, terms
    "user_progress",           # зависит от users, terms, quizzes (теперь ДО quizzes)
    "flashcards",              # зависит от terms
    "user_achievements",       # зависит от users, achievements
    "user_topic_plans",        # зависит от users, topics, grades
    "quizzes",                 # зависит от topics (удаляется ПОСЛЕ user_progress)
    "terms",                   # зависит от domains, topics
    "achievements",
    "topics",                  # зависит от domains
    "grades",
    "domains",
    "topic_generation_sessions", # добавлено для полноты очистки
    "test_runs",
]

@router.post("/reset-data", status_code=status.HTTP_200_OK)
def reset_database(
    confirmation: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Полный сброс всех данных (кроме пользователей).
    Требуется подтверждение строкой "RESET".
    Доступно только для пользователей с email, содержащим "@admin" или "admin@".
    """
    if "admin" not in current_user.email.lower():
        raise HTTPException(status_code=403, detail="Only administrators can reset data")

    if confirmation != "RESET":
        raise HTTPException(status_code=400, detail="Invalid confirmation. Use 'RESET'.")

    deleted_counts = {}
    try:
        # Для PostgreSQL просто удаляем в правильном порядке
        for table in TABLES_IN_ORDER:
            count = db.execute(text(f"DELETE FROM {table}")).rowcount
            deleted_counts[table] = count
            logger.info(f"Deleted {count} rows from {table}")

        db.commit()
        logger.info("Database reset successful, now creating default data...")

        # Создание стандартных записей (домены, грейды, достижения)
        ensure_default_domains(db)
        ensure_default_grades(db)
        init_achievements(db)
        # Каждая из этих функций уже делает commit внутри, поэтому дополнительный commit не нужен
        logger.info("Default data created successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

    return {
        "message": "Database reset successful",
        "deleted": deleted_counts
    }

@router.get("/tables", response_model=schemas.TableListResponse)
def list_tables(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    return {"tables": tables}

@router.get("/table/{table_name}", response_model=schemas.TableDataResponse)
def get_table_data(
    table_name: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    inspector = inspect(db.bind)
    if table_name not in inspector.get_table_names():
        raise HTTPException(status_code=404, detail="Table not found")

    columns = [col['name'] for col in inspector.get_columns(table_name)]

    count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

    result = db.execute(
        text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"),
        {"limit": limit, "offset": offset}
    )
    rows = [dict(row._mapping) for row in result]

    return {
        "table_name": table_name,
        "columns": columns,
        "total": count_result,
        "data": rows,
        "limit": limit,
        "offset": offset
    }