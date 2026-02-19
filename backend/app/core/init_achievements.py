# backend/app/core/init_achievements.py
# Инициализация достижений в базе данных (запускать при старте приложения)

import logging
from sqlalchemy.orm import Session

from app import models

logger = logging.getLogger(__name__)

def init_achievements(db: Session):
    """Создаёт стандартные достижения, если их ещё нет."""
    achievements_data = [
        {
            "name": "Знаток",
            "description": "Просмотрено 100 карточек",
            "condition": {"type": "cards_viewed", "count": 100}
        },
        {
            "name": "Дубль-квиз",
            "description": "Пройдено 2 квиза",
            "condition": {"type": "quizzes_passed", "count": 2}
        },
        {
            "name": "Игрок",
            "description": "Накоплено более 1 XP",
            "condition": {"type": "xp_greater", "value": 2}  # >1 значит >=2
        },
        {
            "name": "Любознательный оптимист",
            "description": "На все термины домена 'Ритейл' ответили «Не знаю»",
            "condition": {"type": "domain_all_unknown", "domain_name": "Ритейл"}
        },
        {
            "name": "Любознательный оптимист (Финтех)",
            "description": "На все термины домена 'Финтех' ответили «Не знаю»",
            "condition": {"type": "domain_all_unknown", "domain_name": "Финтех"}
        }
        # При необходимости добавьте другие домены
    ]

    for data in achievements_data:
        existing = db.query(models.Achievement).filter(
            models.Achievement.name == data["name"]
        ).first()
        if not existing:
            achievement = models.Achievement(
                name=data["name"],
                description=data["description"],
                condition=data["condition"]
            )
            db.add(achievement)
            logger.info(f"Created achievement: {data['name']}")
    db.commit()