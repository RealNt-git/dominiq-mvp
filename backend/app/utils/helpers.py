# backend/app/utils/helpers.py
# Вспомогательные функции

import logging
from sqlalchemy.orm import Session
from app import models

logger = logging.getLogger(__name__)

def calculate_level(xp: int) -> int:
    """Вычисляет уровень на основе опыта."""
    return int((xp // 100) ** 0.5) + 1

def ensure_default_domains(db: Session):
    """
    Проверяет наличие стандартных доменов и создаёт их при необходимости.
    """
    default_domains = ["Ритейл", "Финтех"]
    for name in default_domains:
        domain = db.query(models.Domain).filter(models.Domain.name == name).first()
        if not domain:
            domain = models.Domain(name=name, description=f"Домен {name}")
            db.add(domain)
            logger.info(f"Created default domain: {name}")
    db.commit()