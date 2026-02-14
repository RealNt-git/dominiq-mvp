# backend/app/api/learning.py
# API для обучения: карточки, квизы, прогресс
# Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/learn", tags=["Learning"])

# ---------- Вспомогательные функции ----------
def calculate_next_review(known: bool, repetitions: int, ease_factor: float, interval: int) -> (int, float, int):
    """
    Упрощённая реализация алгоритма SuperMemo-2.
    Возвращает (новый интервал в днях, новый ease_factor, новое количество повторений).
    """
    if known:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(interval * ease_factor)
        repetitions += 1
        # ease_factor не меняем (в классике может меняться, упростим)
    else:
        repetitions = 0
        interval = 1
        # ease_factor можно уменьшить, но оставим как есть
    return interval, ease_factor, repetitions


# ---------- Карточки ----------
@router.get("/cards/due", response_model=List[schemas.CardForReview])
def get_due_cards(
    limit: int = Query(20, description="Максимальное количество карточек"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает список карточек, которые нужно повторить сегодня:
    - новые карточки (нет прогресса)
    - карточки, у которых last_review + interval <= сегодня
    """
    # Получаем все карточки (Flashcard) с подгруженными терминами
    flashcards = db.query(models.Flashcard).all()

    today = date.today()
    due_cards = []

    for flashcard in flashcards:
        # Прогресс пользователя по этой карточке (term_id)
        progress = db.query(models.UserProgress).filter(
            models.UserProgress.user_id == current_user.id,
            models.UserProgress.term_id == flashcard.term_id
        ).first()

        if progress is None:
            # Новая карточка – добавляем
            due_cards.append(flashcard)
        else:
            # Проверяем, пора ли повторять
            if progress.last_review:
                next_review_date = progress.last_review.date() + timedelta(days=progress.interval)
                if next_review_date <= today:
                    due_cards.append(flashcard)

    # Ограничиваем количество
    due_cards = due_cards[:limit]

    # Преобразуем в схему CardForReview
    result = []
    for fc in due_cards:
        term = fc.term
        result.append(schemas.CardForReview(
            id=fc.id,
            term=term.term,
            definition=term.definition,
            example=term.example,
            simplified_definition=fc.simplified_definition,
            hint=fc.hint
        ))
    return result


@router.post("/cards/review", status_code=200)
def review_card(
    review: schemas.CardReviewRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Принимает результат повторения карточки.
    Обновляет прогресс по алгоритму SuperMemo-2 и начисляет XP.
    """
    flashcard = db.query(models.Flashcard).filter(models.Flashcard.id == review.card_id).first()
    if not flashcard:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    term_id = flashcard.term_id

    # Получаем или создаём прогресс
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == current_user.id,
        models.UserProgress.term_id == term_id
    ).first()

    if progress is None:
        progress = models.UserProgress(
            user_id=current_user.id,
            term_id=term_id,
            last_review=None,
            ease_factor=2.5,
            interval=0,
            repetitions=0,
            correct_streak=0,
            total_attempts=0
        )
        db.add(progress)
        db.flush()

    # Обновляем статистику
    progress.total_attempts += 1

    # Применяем алгоритм SM-2
    new_interval, new_ease, new_repetitions = calculate_next_review(
        known=review.known,
        repetitions=progress.repetitions,
        ease_factor=progress.ease_factor,
        interval=progress.interval
    )
    progress.interval = new_interval
    progress.ease_factor = new_ease
    progress.repetitions = new_repetitions
    progress.last_review = date.today()

    # Начисляем XP
    xp_earned = 10 if review.known else 2
    current_user.total_xp += xp_earned
    # Пересчёт уровня (можно вынести в отдельную функцию)
    current_user.level = int((current_user.total_xp // 100) + 1)

    db.commit()

    return {"xp_earned": xp_earned, "new_level": current_user.level}


# ---------- Квизы ----------
@router.get("/quiz/{quiz_id}", response_model=List[schemas.QuizQuestionForUser])
def get_quiz_questions(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает вопросы квиза (без правильных ответов).
    """
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = db.query(models.Question).filter(models.Question.quiz_id == quiz_id).all()
    result = []
    for q in questions:
        result.append(schemas.QuizQuestionForUser(
            id=q.id,
            text=q.text,
            type=q.type,
            options=q.options  # варианты ответов (без correct_answer)
        ))
    return result


@router.post("/quiz/submit", response_model=schemas.QuizResult)
def submit_quiz(
    submission: schemas.QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Принимает ответы на квиз, сравнивает с правильными, начисляет XP.
    Возвращает количество правильных ответов и полученный опыт.
    """
    quiz = db.query(models.Quiz).filter(models.Quiz.id == submission.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = db.query(models.Question).filter(models.Question.quiz_id == submission.quiz_id).all()
    if len(questions) != len(submission.answers):
        raise HTTPException(status_code=400, detail="Number of answers does not match number of questions")

    correct_count = 0
    for q, ans in zip(questions, submission.answers):
        # Сравниваем в зависимости от типа вопроса
        # В MVP только тип "single" (индекс правильного ответа)
        if q.type == "single":
            if isinstance(ans, int) and ans == q.correct_answer:
                correct_count += 1
        # Для других типов можно добавить позже

    # Начисляем XP: например, по 10 за каждый правильный
    xp_earned = correct_count * 10
    current_user.total_xp += xp_earned
    current_user.level = int((current_user.total_xp // 100) + 1)

    # Можно сохранить результат прохождения квиза (но пока не обязательно)
    # Например, создать запись в UserProgress с quiz_id, но для MVP пропустим.

    db.commit()

    return schemas.QuizResult(
        quiz_id=quiz.id,
        correct_count=correct_count,
        total_count=len(questions),
        xp_earned=xp_earned
    )