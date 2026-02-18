# backend/app/api/auth.py
# Упрощённая аутентификация по email
# Исправлен циклический импорт

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas

if TYPE_CHECKING:
    from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


async def get_current_user(
    x_user_email: str = Header(..., alias="X-User-Email"),
    db: Session = Depends(get_db)
) -> "User":
    """
    Возвращает пользователя по email из заголовка.
    Если пользователя нет, создаёт нового.
    """
    from app.models import User  # локальный импорт внутри функции
    user = db.query(User).filter(User.email == x_user_email).first()
    if not user:
        user = User(email=x_user_email)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Auto-created user with email: {x_user_email}")
    return user


@router.post("/login", response_model=schemas.UserOut)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Принимает email, возвращает пользователя (создаёт, если не существует).
    """
    try:
        logger.info(f"Login attempt for email: {user.email}")
        from app.models import User
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user:
            logger.info(f"User not found, creating new user: {user.email}")
            db_user = User(email=user.email)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            logger.info(f"User created with id: {db_user.id}")
        else:
            logger.info(f"User found: {db_user.id}")
        return db_user
    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")