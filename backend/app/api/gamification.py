# backend/app/api/gamification.py
# API для геймификации: прогресс, достижения, уровни
# Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0
# Исправлен подсчёт пройденных квизов
# Добавлена автоматическая проверка и выдача достижений при запросе прогресса

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app import models, schemas
from app.services.achievement_checker import AchievementChecker

router = APIRouter(tags=["Gamification"])


def calculate_level(total_xp: int) -> int:
    if total_xp < 0:
        return 1
    level = int((total_xp // 100) ** 0.5) + 1
    return max(1, level)


@router.get("/progress", response_model=schemas.UserProgressSummary)
def get_user_progress(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает сводку по прогрессу пользователя:
    - total_xp: общее количество опыта
    - level: текущий уровень
    - cards_studied: количество уникальных терминов, по которым были повторения
    - quizzes_passed: количество пройденных квизов
    - achievements_count: количество полученных достижений
    """
    # Проверяем и выдаём достижения на основе текущего прогресса
    checker = AchievementChecker(db, current_user)
    checker.check_and_award()

    cards_studied = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == current_user.id,
        models.UserProgress.term_id.isnot(None)
    ).count()

    # Количество пройденных квизов – считаем записи с quiz_id
    quizzes_passed = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == current_user.id,
        models.UserProgress.quiz_id.isnot(None)
    ).distinct(models.UserProgress.quiz_id).count()

    achievements_count = db.query(models.UserAchievement).filter(
        models.UserAchievement.user_id == current_user.id
    ).count()

    return schemas.UserProgressSummary(
        total_xp=current_user.total_xp,
        level=current_user.level,
        cards_studied=cards_studied,
        quizzes_passed=quizzes_passed,
        achievements_count=achievements_count
    )


@router.get("/achievements", response_model=List[schemas.AchievementWithEarned])
def get_achievements(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Также проверяем достижения при запросе списка, чтобы они были актуальны
    checker = AchievementChecker(db, current_user)
    checker.check_and_award()

    achievements = db.query(models.Achievement).all()
    earned_ids = {
        ua.achievement_id for ua in db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == current_user.id
        )
    }

    result = []
    for ach in achievements:
        earned = ach.id in earned_ids
        earned_at = None
        if earned:
            ua = db.query(models.UserAchievement).filter(
                models.UserAchievement.user_id == current_user.id,
                models.UserAchievement.achievement_id == ach.id
            ).first()
            earned_at = ua.earned_at if ua else None

        result.append(schemas.AchievementWithEarned(
            id=ach.id,
            name=ach.name,
            description=ach.description,
            icon_url=ach.icon_url,
            condition=ach.condition,
            earned=earned,
            earned_at=earned_at
        ))

    return result


@router.post("/xp/add", status_code=200)
def add_xp(
    xp: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if xp <= 0:
        raise HTTPException(status_code=400, detail="XP must be positive")

    current_user.total_xp += xp
    new_level = calculate_level(current_user.total_xp)
    if new_level != current_user.level:
        current_user.level = new_level

    db.commit()
    return {"xp_added": xp, "new_total_xp": current_user.total_xp, "new_level": current_user.level}