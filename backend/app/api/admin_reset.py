###backend/app/api/admin_reset.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.api.auth import get_current_user
from app import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

# Список таблиц в порядке удаления (сначала зависимые)
TABLES_IN_ORDER = [
    "draft_quizzes",
    "draft_terms",
    "documents",
    "processing_progress",
    "questions",
    "quizzes",
    "flashcards",
    "terms",
    "user_progress",
    "user_achievements",
    "achievements",
    "user_topic_plans",
    "grades",
    "topics",
    "domains",
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
    # Простейшая проверка прав (можно заменить на более строгую)
    if "admin" not in current_user.email.lower():
        raise HTTPException(status_code=403, detail="Only administrators can reset data")

    if confirmation != "RESET":
        raise HTTPException(status_code=400, detail="Invalid confirmation. Use 'RESET'.")

    # Отключаем проверку внешних ключей для SQLite (чтобы удалять в любом порядке)
    db.execute(text("PRAGMA foreign_keys=OFF"))

    deleted_counts = {}
    try:
        for table in TABLES_IN_ORDER:
            count = db.execute(text(f"DELETE FROM {table}")).rowcount
            deleted_counts[table] = count
            logger.info(f"Deleted {count} rows from {table}")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")
    finally:
        # Включаем обратно проверку внешних ключей
        db.execute(text("PRAGMA foreign_keys=ON"))

    return {
        "message": "Database reset successful",
        "deleted": deleted_counts
    }