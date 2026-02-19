# backend/app/api/plan.py
# Эндпоинты для управления планами развития пользователей
# Добавлено подробное логирование, прогресс изучения и вложенные объекты

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.api.auth import get_current_user
from app import models, schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["Plans"])


# --- Административные эндпоинты (только для методолога) ---

@router.get("/users", response_model=List[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Список всех пользователей (для методолога)"""
    logger.info(f"User {current_user.email} requested list of all users")
    users = db.query(models.User).all()
    logger.info(f"Returning {len(users)} users")
    return users


@router.get("/topics", response_model=List[schemas.TopicOut])
def list_topics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Список всех тем (для методолога)"""
    logger.info(f"User {current_user.email} requested list of all topics")
    topics = db.query(models.Topic).all()
    logger.info(f"Returning {len(topics)} topics")
    return topics


@router.get("/grades", response_model=List[schemas.GradeOut])
def list_grades(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Список грейдов"""
    logger.info(f"User {current_user.email} requested list of grades")
    grades = db.query(models.Grade).all()
    logger.info(f"Returning {len(grades)} grades")
    return grades


@router.get("/", response_model=List[schemas.UserTopicPlanOut])
def list_plans(
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Список планов, опционально фильтр по пользователю"""
    logger.info(f"User {current_user.email} requested plans list with filter user_id={user_id}")
    query = db.query(models.UserTopicPlan)
    if user_id:
        query = query.filter(models.UserTopicPlan.user_id == user_id)
    plans = query.all()
    logger.info(f"Returning {len(plans)} plans")
    return plans


@router.post("/", response_model=schemas.UserTopicPlanOut, status_code=201)
def create_plan(
    plan: schemas.UserTopicPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новый план для пользователя"""
    logger.info(f"User {current_user.email} creating new plan for user_id={plan.user_id}, topic_id={plan.topic_id}")

    user = db.query(models.User).filter(models.User.id == plan.user_id).first()
    if not user:
        logger.warning(f"User {plan.user_id} not found")
        raise HTTPException(404, "User not found")
    topic = db.query(models.Topic).filter(models.Topic.id == plan.topic_id).first()
    if not topic:
        logger.warning(f"Topic {plan.topic_id} not found")
        raise HTTPException(404, "Topic not found")
    grade = db.query(models.Grade).filter(models.Grade.id == plan.grade_id).first()
    if not grade:
        logger.warning(f"Grade {plan.grade_id} not found")
        raise HTTPException(404, "Grade not found")

    existing = db.query(models.UserTopicPlan).filter(
        models.UserTopicPlan.user_id == plan.user_id,
        models.UserTopicPlan.topic_id == plan.topic_id
    ).first()
    if existing:
        logger.warning(f"Plan for user {plan.user_id} and topic {plan.topic_id} already exists")
        raise HTTPException(400, "Plan for this user and topic already exists")

    db_plan = models.UserTopicPlan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    logger.info(f"Plan created with id {db_plan.id}")
    return db_plan


@router.put("/{plan_id}", response_model=schemas.UserTopicPlanOut)
def update_plan(
    plan_id: int,
    plan_update: schemas.UserTopicPlanUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновить существующий план"""
    logger.info(f"User {current_user.email} updating plan {plan_id}")
    db_plan = db.query(models.UserTopicPlan).filter(models.UserTopicPlan.id == plan_id).first()
    if not db_plan:
        logger.warning(f"Plan {plan_id} not found")
        raise HTTPException(404, "Plan not found")

    for key, value in plan_update.dict(exclude_unset=True).items():
        setattr(db_plan, key, value)
    db.commit()
    db.refresh(db_plan)
    logger.info(f"Plan {plan_id} updated successfully")
    return db_plan


@router.delete("/{plan_id}", status_code=204)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удалить план"""
    logger.info(f"User {current_user.email} deleting plan {plan_id}")
    db_plan = db.query(models.UserTopicPlan).filter(models.UserTopicPlan.id == plan_id).first()
    if not db_plan:
        logger.warning(f"Plan {plan_id} not found")
        raise HTTPException(404, "Plan not found")
    db.delete(db_plan)
    db.commit()
    logger.info(f"Plan {plan_id} deleted")
    return


# --- Пользовательские эндпоинты ---

@router.get("/my", response_model=List[schemas.UserTopicPlanWithProgress])
def get_my_plans(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает план развития текущего пользователя с прогрессом изучения и вложенными объектами.
    Для каждого плана вычисляется:
    - total_terms: общее количество терминов в теме
    - studied_terms: сколько терминов из этой темы пользователь уже изучал
    - также загружаются связанные объекты: topic, grade (user может быть не нужен)
    """
    logger.info(f"User {current_user.email} requesting their own plans with progress and nested objects")

    # Получаем активные планы пользователя с подгрузкой связанных объектов (topic, grade)
    plans = db.query(models.UserTopicPlan).options(
        joinedload(models.UserTopicPlan.topic),
        joinedload(models.UserTopicPlan.grade)
    ).filter(
        models.UserTopicPlan.user_id == current_user.id,
        models.UserTopicPlan.status == "active"
    ).order_by(models.UserTopicPlan.priority).all()

    logger.debug(f"Found {len(plans)} active plans for user {current_user.id}")

    result = []
    for plan in plans:
        logger.debug(f"Processing plan id={plan.id}, topic_id={plan.topic_id}, grade_id={plan.grade_id}")

        # Общее количество терминов в теме
        total_terms = db.query(models.Term).filter(
            models.Term.topic_id == plan.topic_id
        ).count()
        logger.debug(f"Topic {plan.topic_id} has {total_terms} terms")

        # Количество терминов из этой темы, которые пользователь уже знает (repetitions > 0)
        # Исправлено: теперь считаются только те термины, по которым есть прогресс и последний ответ был "знаю"
        studied_terms = db.query(models.UserProgress).join(
            models.Term, models.UserProgress.term_id == models.Term.id
        ).filter(
            models.Term.topic_id == plan.topic_id,
            models.UserProgress.user_id == current_user.id,
            models.UserProgress.repetitions > 0   # добавлено условие для учёта только "знаю"
        ).count()
        logger.debug(f"User studied {studied_terms} terms for topic {plan.topic_id}")

        # Формируем словарь с данными плана
        plan_data = {
            "id": plan.id,
            "user_id": plan.user_id,
            "topic_id": plan.topic_id,
            "grade_id": plan.grade_id,
            "priority": plan.priority,
            "target_date": plan.target_date,
            "status": plan.status,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "total_terms": total_terms,
            "studied_terms": studied_terms,
            # Вложенные объекты
            "topic": plan.topic,
            "grade": plan.grade,
            # "user" не включаем, так как это текущий пользователь
        }
        result.append(plan_data)

    logger.info(f"Returning {len(result)} plans with progress for user {current_user.id}")
    return result