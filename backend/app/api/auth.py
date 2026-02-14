# backend/app/api/auth.py
# Упрощённая аутентификация по email

import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

# Зависимость для получения текущего пользователя по заголовку X-User-Email
async def get_current_user(
    x_user_email: str = Header(..., alias="X-User-Email"),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Возвращает пользователя по email из заголовка.
    Если пользователя нет, создаёт нового.
    """
    user = db.query(models.User).filter(models.User.email == x_user_email).first()
    if not user:
        user = models.User(email=x_user_email)
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
        db_user = db.query(models.User).filter(models.User.email == user.email).first()
        if not db_user:
            logger.info(f"User not found, creating new user: {user.email}")
            db_user = models.User(email=user.email)
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