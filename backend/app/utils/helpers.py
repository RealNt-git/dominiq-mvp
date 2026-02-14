# backend/app/utils/helpers.py
# Вспомогательные функции (опционально)

def calculate_level(xp: int) -> int:
    """Вычисляет уровень на основе опыта."""
    return int((xp // 100) ** 0.5) + 1