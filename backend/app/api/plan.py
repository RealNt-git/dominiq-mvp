# backend/app/api/plan.py
# Эндпоинты для управления планами развития пользователей

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/plans", tags=["Plans"])


# --- Административные эндпоинты (только для методолога) ---
# Для упрощения проверку роли пока пропустим, добавим позже

@router.get("/users", response_model=List[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Список всех пользователей (для методолога)"""
    return db.query(models.User).all()


@router.get("/topics", response_model=List[schemas.TopicOut])
def list_topics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Список всех тем (для методолога)"""
    return db.query(models.Topic).all()


@router.get("/grades", response_model=List[schemas.GradeOut])
def list_grades(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Список грейдов"""
    grades = db.query(models.Grade).all()
    return grades


@router.get("/", response_model=List[schemas.UserTopicPlanOut])
def list_plans(
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Список планов, опционально фильтр по пользователю"""
    query = db.query(models.UserTopicPlan)
    if user_id:
        query = query.filter(models.UserTopicPlan.user_id == user_id)
    return query.all()


@router.post("/", response_model=schemas.UserTopicPlanOut, status_code=201)
def create_plan(
    plan: schemas.UserTopicPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новый план для пользователя"""
    # Проверим, что пользователь, тема и грейд существуют
    user = db.query(models.User).filter(models.User.id == plan.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    topic = db.query(models.Topic).filter(models.Topic.id == plan.topic_id).first()
    if not topic:
        raise HTTPException(404, "Topic not found")
    grade = db.query(models.Grade).filter(models.Grade.id == plan.grade_id).first()
    if not grade:
        raise HTTPException(404, "Grade not found")

    # Проверим, что такой план ещё не существует (уникальность user_id+topic_id)
    existing = db.query(models.UserTopicPlan).filter(
        models.UserTopicPlan.user_id == plan.user_id,
        models.UserTopicPlan.topic_id == plan.topic_id
    ).first()
    if existing:
        raise HTTPException(400, "Plan for this user and topic already exists")

    db_plan = models.UserTopicPlan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.put("/{plan_id}", response_model=schemas.UserTopicPlanOut)
def update_plan(
    plan_id: int,
    plan_update: schemas.UserTopicPlanUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновить существующий план"""
    db_plan = db.query(models.UserTopicPlan).filter(models.UserTopicPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(404, "Plan not found")
    for key, value in plan_update.dict(exclude_unset=True).items():
        setattr(db_plan, key, value)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.delete("/{plan_id}", status_code=204)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удалить план"""
    db_plan = db.query(models.UserTopicPlan).filter(models.UserTopicPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(404, "Plan not found")
    db.delete(db_plan)
    db.commit()
    return


# --- Пользовательские эндпоинты ---

@router.get("/my", response_model=List[schemas.UserTopicPlanOut])
def get_my_plans(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Возвращает план развития текущего пользователя"""
    plans = db.query(models.UserTopicPlan).filter(
        models.UserTopicPlan.user_id == current_user.id,
        models.UserTopicPlan.status == "active"
    ).order_by(models.UserTopicPlan.priority).all()
    return plans