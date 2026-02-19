# backend/app/services/achievement_checker.py
# Сервис для проверки и выдачи достижений
# Добавлен в проект для автоматической геймификации

import logging
from sqlalchemy.orm import Session

from app import models

logger = logging.getLogger(__name__)

class AchievementChecker:
    """Класс для проверки условий достижений и их выдачи."""

    def __init__(self, db: Session, user: models.User):
        self.db = db
        self.user = user

    def check_and_award(self):
        """Проверяет все достижения и выдаёт те, которые ещё не получены."""
        achievements = self.db.query(models.Achievement).all()
        for ach in achievements:
            # Пропускаем уже полученные
            already = self.db.query(models.UserAchievement).filter(
                models.UserAchievement.user_id == self.user.id,
                models.UserAchievement.achievement_id == ach.id
            ).first()
            if already:
                continue

            condition = ach.condition
            if not condition:
                continue

            # Определяем тип условия и проверяем
            if condition.get("type") == "cards_viewed":
                if self._check_cards_viewed(condition.get("count", 0)):
                    self._award(ach)
            elif condition.get("type") == "quizzes_passed":
                if self._check_quizzes_passed(condition.get("count", 0)):
                    self._award(ach)
            elif condition.get("type") == "xp_greater":
                if self._check_xp_greater(condition.get("value", 0)):
                    self._award(ach)
            elif condition.get("type") == "domain_all_unknown":
                if self._check_domain_all_unknown(condition.get("domain_name")):
                    self._award(ach)
            # можно добавить другие типы

    def _award(self, achievement: models.Achievement):
        """Выдаёт достижение пользователю."""
        ua = models.UserAchievement(
            user_id=self.user.id,
            achievement_id=achievement.id
        )
        self.db.add(ua)
        self.db.commit()
        logger.info(f"User {self.user.email} earned achievement '{achievement.name}'")

    def _check_cards_viewed(self, required_count: int) -> bool:
        """Проверяет, просмотрено ли достаточное количество карточек (суммарно total_attempts)."""
        total_attempts = self.db.query(models.UserProgress).filter(
            models.UserProgress.user_id == self.user.id,
            models.UserProgress.term_id.isnot(None)
        ).with_entities(models.UserProgress.total_attempts).all()
        total = sum([ta for (ta,) in total_attempts])
        return total >= required_count

    def _check_quizzes_passed(self, required_count: int) -> bool:
        """Проверяет количество пройденных квизов (уникальных quiz_id)."""
        count = self.db.query(models.UserProgress).filter(
            models.UserProgress.user_id == self.user.id,
            models.UserProgress.quiz_id.isnot(None)
        ).distinct(models.UserProgress.quiz_id).count()
        return count >= required_count

    def _check_xp_greater(self, required_xp: int) -> bool:
        """Проверяет, превышает ли общий XP порог."""
        return self.user.total_xp >= required_xp

    def _check_domain_all_unknown(self, domain_name: str) -> bool:
        """
        Проверяет, что по всем терминам указанного домена есть хотя бы один ответ "Не знаю".
        Для этого проверяем, что по каждому термину домена есть прогресс с repetitions == 0.
        """
        # Находим все термины домена
        terms = self.db.query(models.Term).join(models.Domain).filter(
            models.Domain.name == domain_name
        ).all()
        if not terms:
            return False

        # Для каждого термина проверяем, есть ли у пользователя прогресс с repetitions == 0
        for term in terms:
            progress = self.db.query(models.UserProgress).filter(
                models.UserProgress.user_id == self.user.id,
                models.UserProgress.term_id == term.id
            ).first()
            if not progress or progress.repetitions != 0:
                # либо прогресса нет, либо последний ответ был "знаю" (repetitions > 0)
                return False
        return True