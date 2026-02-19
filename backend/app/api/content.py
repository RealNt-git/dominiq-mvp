# backend/app/api/content.py
# Модуль API для управления контентом (термины, темы, квизы)
# Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0
# Добавлено подробное логирование всех эндпоинтов с extra-полями для Kibana

from __future__ import annotations

from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import schemas
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)


# ---------- Роутеры для каждой сущности ----------
domains_router = APIRouter(prefix="/domains", tags=["Domains"])
topics_router = APIRouter(prefix="/topics", tags=["Topics"])
terms_router = APIRouter(prefix="/terms", tags=["Terms"])
flashcards_router = APIRouter(prefix="/flashcards", tags=["Flashcards"])
quizzes_router = APIRouter(prefix="/quizzes", tags=["Quizzes"])
questions_router = APIRouter(prefix="/questions", tags=["Questions"])

# ---------- Вспомогательные функции ----------
def get_domain_or_404(db: Session, domain_id: int) -> "models.Domain":
    from app import models
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        logger.warning("Domain not found", extra={
            "action": "get_domain_or_404",
            "domain_id": domain_id,
            "status": 404
        })
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain

def get_topic_or_404(db: Session, topic_id: int) -> "models.Topic":
    from app import models
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        logger.warning("Topic not found", extra={
            "action": "get_topic_or_404",
            "topic_id": topic_id,
            "status": 404
        })
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

def get_term_or_404(db: Session, term_id: int) -> "models.Term":
    from app import models
    term = db.query(models.Term).filter(models.Term.id == term_id).first()
    if not term:
        logger.warning("Term not found", extra={
            "action": "get_term_or_404",
            "term_id": term_id,
            "status": 404
        })
        raise HTTPException(status_code=404, detail="Term not found")
    return term

def get_flashcard_or_404(db: Session, flashcard_id: int) -> "models.Flashcard":
    from app import models
    flashcard = db.query(models.Flashcard).filter(models.Flashcard.id == flashcard_id).first()
    if not flashcard:
        logger.warning("Flashcard not found", extra={
            "action": "get_flashcard_or_404",
            "flashcard_id": flashcard_id,
            "status": 404
        })
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return flashcard

def get_quiz_or_404(db: Session, quiz_id: int) -> "models.Quiz":
    from app import models
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        logger.warning("Quiz not found", extra={
            "action": "get_quiz_or_404",
            "quiz_id": quiz_id,
            "status": 404
        })
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

def get_question_or_404(db: Session, question_id: int) -> "models.Question":
    from app import models
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        logger.warning("Question not found", extra={
            "action": "get_question_or_404",
            "question_id": question_id,
            "status": 404
        })
        raise HTTPException(status_code=404, detail="Question not found")
    return question


# ---------- Domains ----------
@domains_router.get("/", response_model=List[schemas.DomainOut])
def list_domains(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить список всех доменов."""
    logger.info("Listing domains", extra={
        "user_email": current_user.email,
        "action": "list_domains"
    })
    from app import models
    domains = db.query(models.Domain).all()
    logger.info("Domains listed", extra={
        "user_email": current_user.email,
        "action": "list_domains",
        "count": len(domains)
    })
    return domains


@domains_router.post("/", response_model=schemas.DomainOut, status_code=status.HTTP_201_CREATED)
def create_domain(
    domain: schemas.DomainCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Создать новый домен."""
    logger.info("Creating domain", extra={
        "user_email": current_user.email,
        "action": "create_domain",
        "domain_name": domain.name
    })
    from app import models
    from app.utils.helpers import get_or_create_general_topic
    db_domain = models.Domain(**domain.dict())
    db.add(db_domain)
    db.flush()
    # Создаём тему "Общая"
    get_or_create_general_topic(db, domain.name, db_domain.id)
    db.commit()
    db.refresh(db_domain)
    logger.info("Domain created", extra={
        "user_email": current_user.email,
        "action": "create_domain",
        "domain_id": db_domain.id,
        "domain_name": db_domain.name
    })
    return db_domain


@domains_router.put("/{domain_id}", response_model=schemas.DomainOut)
def update_domain(
    domain_id: int,
    domain_update: schemas.DomainUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обновить существующий домен."""
    logger.info("Updating domain", extra={
        "user_email": current_user.email,
        "action": "update_domain",
        "domain_id": domain_id
    })
    db_domain = get_domain_or_404(db, domain_id)
    update_data = domain_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_domain, key, value)
    db.commit()
    db.refresh(db_domain)
    logger.info("Domain updated", extra={
        "user_email": current_user.email,
        "action": "update_domain",
        "domain_id": domain_id,
        "updated_fields": list(update_data.keys())
    })
    return db_domain


@domains_router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Удалить домен."""
    logger.info("Deleting domain", extra={
        "user_email": current_user.email,
        "action": "delete_domain",
        "domain_id": domain_id
    })
    db_domain = get_domain_or_404(db, domain_id)
    db.delete(db_domain)
    db.commit()
    logger.info("Domain deleted", extra={
        "user_email": current_user.email,
        "action": "delete_domain",
        "domain_id": domain_id
    })
    return


# ---------- Topics ----------
@topics_router.get("/", response_model=List[schemas.TopicOut])
def list_topics(
    domain_id: Optional[int] = Query(None, description="Фильтр по домену"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить список тем. Можно фильтровать по domain_id."""
    logger.info("Listing topics", extra={
        "user_email": current_user.email,
        "action": "list_topics",
        "filter_domain_id": domain_id
    })
    from app import models
    query = db.query(models.Topic)
    if domain_id:
        query = query.filter(models.Topic.domain_id == domain_id)
    topics = query.all()
    logger.info("Topics listed", extra={
        "user_email": current_user.email,
        "action": "list_topics",
        "filter_domain_id": domain_id,
        "count": len(topics)
    })
    return topics


@topics_router.post("/", response_model=schemas.TopicOut, status_code=status.HTTP_201_CREATED)
def create_topic(
    topic: schemas.TopicCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Создать новую тему."""
    logger.info("Creating topic", extra={
        "user_email": current_user.email,
        "action": "create_topic",
        "topic_name": topic.name,
        "domain_id": topic.domain_id,
        "parent_id": topic.parent_id
    })
    # Проверка существования домена
    get_domain_or_404(db, topic.domain_id)
    # Проверка parent_id, если указан
    if topic.parent_id:
        get_topic_or_404(db, topic.parent_id)
    from app import models
    db_topic = models.Topic(**topic.dict())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    logger.info("Topic created", extra={
        "user_email": current_user.email,
        "action": "create_topic",
        "topic_id": db_topic.id,
        "topic_name": db_topic.name
    })
    return db_topic


@topics_router.put("/{topic_id}", response_model=schemas.TopicOut)
def update_topic(
    topic_id: int,
    topic_update: schemas.TopicUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обновить тему."""
    logger.info("Updating topic", extra={
        "user_email": current_user.email,
        "action": "update_topic",
        "topic_id": topic_id
    })
    db_topic = get_topic_or_404(db, topic_id)
    update_data = topic_update.dict(exclude_unset=True)
    # Если обновляется domain_id, проверить существование
    if "domain_id" in update_data and update_data["domain_id"] is not None:
        get_domain_or_404(db, update_data["domain_id"])
    # Если обновляется parent_id, проверить
    if "parent_id" in update_data and update_data["parent_id"] is not None:
        get_topic_or_404(db, update_data["parent_id"])
    for key, value in update_data.items():
        setattr(db_topic, key, value)
    db.commit()
    db.refresh(db_topic)
    logger.info("Topic updated", extra={
        "user_email": current_user.email,
        "action": "update_topic",
        "topic_id": topic_id,
        "updated_fields": list(update_data.keys())
    })
    return db_topic


@topics_router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Удалить тему."""
    logger.info("Deleting topic", extra={
        "user_email": current_user.email,
        "action": "delete_topic",
        "topic_id": topic_id
    })
    db_topic = get_topic_or_404(db, topic_id)
    db.delete(db_topic)
    db.commit()
    logger.info("Topic deleted", extra={
        "user_email": current_user.email,
        "action": "delete_topic",
        "topic_id": topic_id
    })
    return


# ---------- Terms ----------
@terms_router.get("/", response_model=List[schemas.TermWithQuestions])
def list_terms(
    domain_id: Optional[int] = Query(None, description="Фильтр по домену"),
    topic_id: Optional[int] = Query(None, description="Фильтр по теме"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить список терминов с вложенными вопросами."""
    logger.info("Listing terms with questions", extra={
        "user_email": current_user.email,
        "action": "list_terms",
        "filter_domain_id": domain_id,
        "filter_topic_id": topic_id
    })
    from app import models
    query = db.query(models.Term)
    if domain_id:
        query = query.filter(models.Term.domain_id == domain_id)
    if topic_id:
        query = query.filter(models.Term.topic_id == topic_id)
    terms = query.all()
    logger.info(f"Found {len(terms)} terms", extra={
        "user_email": current_user.email,
        "action": "list_terms",
        "filter_domain_id": domain_id,
        "filter_topic_id": topic_id,
        "terms_count": len(terms)
    })

    result = []
    for term in terms:
        questions = db.query(models.Question).filter(models.Question.term_id == term.id).all()
        term_data = schemas.TermOut.from_orm(term)
        term_with_questions = schemas.TermWithQuestions(
            **term_data.dict(),
            questions=[schemas.QuestionOut.from_orm(q) for q in questions]
        )
        result.append(term_with_questions)
        logger.debug(f"Term '{term.term}' (id={term.id}) has {len(questions)} questions")

    logger.info("Terms with questions listed", extra={
        "user_email": current_user.email,
        "action": "list_terms",
        "filter_domain_id": domain_id,
        "filter_topic_id": topic_id,
        "returned_count": len(result)
    })
    return result


@terms_router.post("/", response_model=schemas.TermOut, status_code=status.HTTP_201_CREATED)
def create_term(
    term: schemas.TermCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Создать новый термин."""
    logger.info("Creating term", extra={
        "user_email": current_user.email,
        "action": "create_term",
        "term": term.term,
        "domain_id": term.domain_id,
        "topic_id": term.topic_id
    })
    # Проверка домена
    get_domain_or_404(db, term.domain_id)
    # Проверка темы, если указана
    if term.topic_id:
        get_topic_or_404(db, term.topic_id)
    from app import models
    db_term = models.Term(**term.dict())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    logger.info("Term created", extra={
        "user_email": current_user.email,
        "action": "create_term",
        "term_id": db_term.id,
        "term": db_term.term
    })
    return db_term


@terms_router.put("/{term_id}", response_model=schemas.TermOut)
def update_term(
    term_id: int,
    term_update: schemas.TermUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обновить термин."""
    logger.info("Updating term", extra={
        "user_email": current_user.email,
        "action": "update_term",
        "term_id": term_id
    })
    db_term = get_term_or_404(db, term_id)
    update_data = term_update.dict(exclude_unset=True)
    # Проверка домена, если обновляется
    if "domain_id" in update_data and update_data["domain_id"] is not None:
        get_domain_or_404(db, update_data["domain_id"])
    # Проверка темы, если обновляется
    if "topic_id" in update_data and update_data["topic_id"] is not None:
        get_topic_or_404(db, update_data["topic_id"])
    for key, value in update_data.items():
        setattr(db_term, key, value)
    db.commit()
    db.refresh(db_term)
    logger.info("Term updated", extra={
        "user_email": current_user.email,
        "action": "update_term",
        "term_id": term_id,
        "updated_fields": list(update_data.keys())
    })
    return db_term


@terms_router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_term(
    term_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Удалить термин."""
    logger.info("Deleting term", extra={
        "user_email": current_user.email,
        "action": "delete_term",
        "term_id": term_id
    })
    db_term = get_term_or_404(db, term_id)
    db.delete(db_term)
    db.commit()
    logger.info("Term deleted", extra={
        "user_email": current_user.email,
        "action": "delete_term",
        "term_id": term_id
    })
    return


# ---------- Flashcards ----------
@flashcards_router.get("/", response_model=List[schemas.FlashcardOut])
def list_flashcards(
    term_id: Optional[int] = Query(None, description="Фильтр по термину"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить список карточек. Можно фильтровать по term_id."""
    logger.info("Listing flashcards", extra={
        "user_email": current_user.email,
        "action": "list_flashcards",
        "filter_term_id": term_id
    })
    from app import models
    query = db.query(models.Flashcard)
    if term_id:
        query = query.filter(models.Flashcard.term_id == term_id)
    flashcards = query.all()
    logger.info("Flashcards listed", extra={
        "user_email": current_user.email,
        "action": "list_flashcards",
        "filter_term_id": term_id,
        "count": len(flashcards)
    })
    return flashcards


@flashcards_router.post("/", response_model=schemas.FlashcardOut, status_code=status.HTTP_201_CREATED)
def create_flashcard(
    flashcard: schemas.FlashcardCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Создать новую карточку для термина."""
    logger.info("Creating flashcard", extra={
        "user_email": current_user.email,
        "action": "create_flashcard",
        "term_id": flashcard.term_id
    })
    # Проверка существования термина
    get_term_or_404(db, flashcard.term_id)
    # Убедимся, что для этого термина ещё нет карточки (уникальность term_id)
    from app import models
    existing = db.query(models.Flashcard).filter(models.Flashcard.term_id == flashcard.term_id).first()
    if existing:
        logger.warning("Flashcard already exists for term", extra={
            "user_email": current_user.email,
            "action": "create_flashcard",
            "term_id": flashcard.term_id,
            "status": 400
        })
        raise HTTPException(status_code=400, detail="Flashcard for this term already exists")
    db_flashcard = models.Flashcard(**flashcard.dict())
    db.add(db_flashcard)
    db.commit()
    db.refresh(db_flashcard)
    logger.info("Flashcard created", extra={
        "user_email": current_user.email,
        "action": "create_flashcard",
        "flashcard_id": db_flashcard.id,
        "term_id": db_flashcard.term_id
    })
    return db_flashcard


@flashcards_router.put("/{flashcard_id}", response_model=schemas.FlashcardOut)
def update_flashcard(
    flashcard_id: int,
    flashcard_update: schemas.FlashcardUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обновить карточку."""
    logger.info("Updating flashcard", extra={
        "user_email": current_user.email,
        "action": "update_flashcard",
        "flashcard_id": flashcard_id
    })
    db_flashcard = get_flashcard_or_404(db, flashcard_id)
    update_data = flashcard_update.dict(exclude_unset=True)
    if "term_id" in update_data and update_data["term_id"] is not None:
        # Проверяем новый term_id и уникальность
        get_term_or_404(db, update_data["term_id"])
        from app import models
        existing = db.query(models.Flashcard).filter(
            models.Flashcard.term_id == update_data["term_id"],
            models.Flashcard.id != flashcard_id
        ).first()
        if existing:
            logger.warning("Flashcard for new term already exists", extra={
                "user_email": current_user.email,
                "action": "update_flashcard",
                "flashcard_id": flashcard_id,
                "new_term_id": update_data["term_id"],
                "status": 400
            })
            raise HTTPException(status_code=400, detail="Flashcard for this term already exists")
    for key, value in update_data.items():
        setattr(db_flashcard, key, value)
    db.commit()
    db.refresh(db_flashcard)
    logger.info("Flashcard updated", extra={
        "user_email": current_user.email,
        "action": "update_flashcard",
        "flashcard_id": flashcard_id,
        "updated_fields": list(update_data.keys())
    })
    return db_flashcard


@flashcards_router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flashcard(
    flashcard_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Удалить карточку."""
    logger.info("Deleting flashcard", extra={
        "user_email": current_user.email,
        "action": "delete_flashcard",
        "flashcard_id": flashcard_id
    })
    db_flashcard = get_flashcard_or_404(db, flashcard_id)
    db.delete(db_flashcard)
    db.commit()
    logger.info("Flashcard deleted", extra={
        "user_email": current_user.email,
        "action": "delete_flashcard",
        "flashcard_id": flashcard_id
    })
    return


# ---------- Quizzes ----------
@quizzes_router.get("/", response_model=List[schemas.QuizWithTopicDetails])
def list_quizzes(
    topic_id: Optional[int] = Query(None, description="Фильтр по теме"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Получить список квизов с названиями темы и домена.
    Можно фильтровать по topic_id.
    """
    logger.info("Listing quizzes", extra={
        "user_email": current_user.email,
        "action": "list_quizzes",
        "filter_topic_id": topic_id
    })
    from app import models
    query = db.query(models.Quiz).options(
        joinedload(models.Quiz.topic).joinedload(models.Topic.domain)
    )
    if topic_id:
        query = query.filter(models.Quiz.topic_id == topic_id)
    quizzes = query.all()
    result = []
    for q in quizzes:
        topic_name = q.topic.name if q.topic else "Неизвестная тема"
        domain_name = q.topic.domain.name if q.topic and q.topic.domain else "Неизвестный домен"
        result.append({
            "id": q.id,
            "title": q.title,
            "topic_id": q.topic_id,
            "topic_name": topic_name,
            "domain_name": domain_name
        })
    logger.info("Quizzes listed", extra={
        "user_email": current_user.email,
        "action": "list_quizzes",
        "filter_topic_id": topic_id,
        "count": len(result)
    })
    return result


@quizzes_router.post("/", response_model=schemas.QuizOut, status_code=status.HTTP_201_CREATED)
def create_quiz(
    quiz: schemas.QuizCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Создать новый квиз."""
    logger.info("Creating quiz", extra={
        "user_email": current_user.email,
        "action": "create_quiz",
        "quiz_title": quiz.title,
        "topic_id": quiz.topic_id
    })
    # Проверка темы
    get_topic_or_404(db, quiz.topic_id)
    from app import models
    db_quiz = models.Quiz(**quiz.dict())
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    logger.info("Quiz created", extra={
        "user_email": current_user.email,
        "action": "create_quiz",
        "quiz_id": db_quiz.id,
        "quiz_title": db_quiz.title,
        "topic_id": db_quiz.topic_id
    })
    return db_quiz


@quizzes_router.put("/{quiz_id}", response_model=schemas.QuizOut)
def update_quiz(
    quiz_id: int,
    quiz_update: schemas.QuizUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обновить квиз."""
    logger.info("Updating quiz", extra={
        "user_email": current_user.email,
        "action": "update_quiz",
        "quiz_id": quiz_id
    })
    db_quiz = get_quiz_or_404(db, quiz_id)
    update_data = quiz_update.dict(exclude_unset=True)
    if "topic_id" in update_data and update_data["topic_id"] is not None:
        get_topic_or_404(db, update_data["topic_id"])
    for key, value in update_data.items():
        setattr(db_quiz, key, value)
    db.commit()
    db.refresh(db_quiz)
    logger.info("Quiz updated", extra={
        "user_email": current_user.email,
        "action": "update_quiz",
        "quiz_id": quiz_id,
        "updated_fields": list(update_data.keys())
    })
    return db_quiz


@quizzes_router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Удалить квиз (вопросы удалятся каскадно)."""
    logger.info("Deleting quiz", extra={
        "user_email": current_user.email,
        "action": "delete_quiz",
        "quiz_id": quiz_id
    })
    db_quiz = get_quiz_or_404(db, quiz_id)
    db.delete(db_quiz)
    db.commit()
    logger.info("Quiz deleted", extra={
        "user_email": current_user.email,
        "action": "delete_quiz",
        "quiz_id": quiz_id
    })
    return


# ---------- Questions ----------
@questions_router.get("/", response_model=List[schemas.QuestionOut])
def list_questions(
    quiz_id: Optional[int] = Query(None, description="Фильтр по квизу"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить список вопросов. Можно фильтровать по quiz_id."""
    logger.info("Listing questions", extra={
        "user_email": current_user.email,
        "action": "list_questions",
        "filter_quiz_id": quiz_id
    })
    from app import models
    query = db.query(models.Question)
    if quiz_id:
        query = query.filter(models.Question.quiz_id == quiz_id)
    questions = query.all()
    logger.info("Questions listed", extra={
        "user_email": current_user.email,
        "action": "list_questions",
        "filter_quiz_id": quiz_id,
        "count": len(questions)
    })
    return questions


@questions_router.post("/", response_model=schemas.QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Создать новый вопрос."""
    logger.info("Creating question", extra={
        "user_email": current_user.email,
        "action": "create_question",
        "quiz_id": question.quiz_id,
        "question_text": question.text[:50]  # обрезаем для краткости
    })
    # Проверка квиза
    get_quiz_or_404(db, question.quiz_id)
    from app import models
    db_question = models.Question(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    logger.info("Question created", extra={
        "user_email": current_user.email,
        "action": "create_question",
        "question_id": db_question.id,
        "quiz_id": db_question.quiz_id
    })
    return db_question


@questions_router.put("/{question_id}", response_model=schemas.QuestionOut)
def update_question(
    question_id: int,
    question_update: schemas.QuestionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обновить вопрос."""
    logger.info("Updating question", extra={
        "user_email": current_user.email,
        "action": "update_question",
        "question_id": question_id
    })
    db_question = get_question_or_404(db, question_id)
    update_data = question_update.dict(exclude_unset=True)
    if "quiz_id" in update_data and update_data["quiz_id"] is not None:
        get_quiz_or_404(db, update_data["quiz_id"])
    for key, value in update_data.items():
        setattr(db_question, key, value)
    db.commit()
    db.refresh(db_question)
    logger.info("Question updated", extra={
        "user_email": current_user.email,
        "action": "update_question",
        "question_id": question_id,
        "updated_fields": list(update_data.keys())
    })
    return db_question


@questions_router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Удалить вопрос."""
    logger.info("Deleting question", extra={
        "user_email": current_user.email,
        "action": "delete_question",
        "question_id": question_id
    })
    db_question = get_question_or_404(db, question_id)
    db.delete(db_question)
    db.commit()
    logger.info("Question deleted", extra={
        "user_email": current_user.email,
        "action": "delete_question",
        "question_id": question_id
    })
    return


# ---------- Объединение всех роутеров в один для удобного подключения ----------
content_router = APIRouter()
content_router.include_router(domains_router)
content_router.include_router(topics_router)
content_router.include_router(terms_router)
content_router.include_router(flashcards_router)
content_router.include_router(quizzes_router)
content_router.include_router(questions_router)