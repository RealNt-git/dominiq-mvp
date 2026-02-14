# backend/app/api/content.py
# Модуль API для управления контентом (термины, темы, квизы)
# Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.api.auth import get_current_user  # зависимость для получения текущего пользователя (упрощённая)

# ---------- Роутеры для каждой сущности ----------
domains_router = APIRouter(prefix="/domains", tags=["Domains"])
topics_router = APIRouter(prefix="/topics", tags=["Topics"])
terms_router = APIRouter(prefix="/terms", tags=["Terms"])
flashcards_router = APIRouter(prefix="/flashcards", tags=["Flashcards"])
quizzes_router = APIRouter(prefix="/quizzes", tags=["Quizzes"])
questions_router = APIRouter(prefix="/questions", tags=["Questions"])

# ---------- Вспомогательные функции ----------
def get_domain_or_404(db: Session, domain_id: int) -> models.Domain:
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain

def get_topic_or_404(db: Session, topic_id: int) -> models.Topic:
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

def get_term_or_404(db: Session, term_id: int) -> models.Term:
    term = db.query(models.Term).filter(models.Term.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return term

def get_flashcard_or_404(db: Session, flashcard_id: int) -> models.Flashcard:
    flashcard = db.query(models.Flashcard).filter(models.Flashcard.id == flashcard_id).first()
    if not flashcard:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return flashcard

def get_quiz_or_404(db: Session, quiz_id: int) -> models.Quiz:
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

def get_question_or_404(db: Session, question_id: int) -> models.Question:
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

# ---------- Domains ----------
@domains_router.get("/", response_model=List[schemas.DomainOut])
def list_domains(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # защита (в MVP любой пользователь)
):
    """Получить список всех доменов."""
    return db.query(models.Domain).all()

@domains_router.post("/", response_model=schemas.DomainOut, status_code=status.HTTP_201_CREATED)
def create_domain(
    domain: schemas.DomainCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новый домен."""
    db_domain = models.Domain(**domain.dict())
    db.add(db_domain)
    db.commit()
    db.refresh(db_domain)
    return db_domain

@domains_router.put("/{domain_id}", response_model=schemas.DomainOut)
def update_domain(
    domain_id: int,
    domain_update: schemas.DomainUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновить существующий домен."""
    db_domain = get_domain_or_404(db, domain_id)
    for key, value in domain_update.dict(exclude_unset=True).items():
        setattr(db_domain, key, value)
    db.commit()
    db.refresh(db_domain)
    return db_domain

@domains_router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удалить домен."""
    db_domain = get_domain_or_404(db, domain_id)
    db.delete(db_domain)
    db.commit()
    return

# ---------- Topics ----------
@topics_router.get("/", response_model=List[schemas.TopicOut])
def list_topics(
    domain_id: Optional[int] = Query(None, description="Фильтр по домену"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить список тем. Можно фильтровать по domain_id."""
    query = db.query(models.Topic)
    if domain_id:
        query = query.filter(models.Topic.domain_id == domain_id)
    return query.all()

@topics_router.post("/", response_model=schemas.TopicOut, status_code=status.HTTP_201_CREATED)
def create_topic(
    topic: schemas.TopicCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новую тему."""
    # Проверка существования домена
    get_domain_or_404(db, topic.domain_id)
    # Проверка parent_id, если указан
    if topic.parent_id:
        get_topic_or_404(db, topic.parent_id)
    db_topic = models.Topic(**topic.dict())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@topics_router.put("/{topic_id}", response_model=schemas.TopicOut)
def update_topic(
    topic_id: int,
    topic_update: schemas.TopicUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновить тему."""
    db_topic = get_topic_or_404(db, topic_id)
    # Если обновляется domain_id, проверить существование
    if topic_update.domain_id is not None:
        get_domain_or_404(db, topic_update.domain_id)
    # Если обновляется parent_id, проверить
    if topic_update.parent_id is not None:
        get_topic_or_404(db, topic_update.parent_id)
    for key, value in topic_update.dict(exclude_unset=True).items():
        setattr(db_topic, key, value)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@topics_router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удалить тему."""
    db_topic = get_topic_or_404(db, topic_id)
    db.delete(db_topic)
    db.commit()
    return

# ---------- Terms ----------
@terms_router.get("/", response_model=List[schemas.TermOut])
def list_terms(
    domain_id: Optional[int] = Query(None, description="Фильтр по домену"),
    topic_id: Optional[int] = Query(None, description="Фильтр по теме"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить список терминов. Фильтрация по domain_id и/или topic_id."""
    query = db.query(models.Term)
    if domain_id:
        query = query.filter(models.Term.domain_id == domain_id)
    if topic_id:
        query = query.filter(models.Term.topic_id == topic_id)
    return query.all()

@terms_router.post("/", response_model=schemas.TermOut, status_code=status.HTTP_201_CREATED)
def create_term(
    term: schemas.TermCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новый термин."""
    # Проверка домена
    get_domain_or_404(db, term.domain_id)
    # Проверка темы, если указана
    if term.topic_id:
        get_topic_or_404(db, term.topic_id)
    db_term = models.Term(**term.dict())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    return db_term

@terms_router.put("/{term_id}", response_model=schemas.TermOut)
def update_term(
    term_id: int,
    term_update: schemas.TermUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновить термин."""
    db_term = get_term_or_404(db, term_id)
    # Проверка домена, если обновляется
    if term_update.domain_id is not None:
        get_domain_or_404(db, term_update.domain_id)
    # Проверка темы, если обновляется
    if term_update.topic_id is not None:
        get_topic_or_404(db, term_update.topic_id)
    for key, value in term_update.dict(exclude_unset=True).items():
        setattr(db_term, key, value)
    db.commit()
    db.refresh(db_term)
    return db_term

@terms_router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_term(
    term_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удалить термин."""
    db_term = get_term_or_404(db, term_id)
    db.delete(db_term)
    db.commit()
    return

# ---------- Flashcards ----------
@flashcards_router.get("/", response_model=List[schemas.FlashcardOut])
def list_flashcards(
    term_id: Optional[int] = Query(None, description="Фильтр по термину"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить список карточек. Можно фильтровать по term_id."""
    query = db.query(models.Flashcard)
    if term_id:
        query = query.filter(models.Flashcard.term_id == term_id)
    return query.all()

@flashcards_router.post("/", response_model=schemas.FlashcardOut, status_code=status.HTTP_201_CREATED)
def create_flashcard(
    flashcard: schemas.FlashcardCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новую карточку для термина."""
    # Проверка существования термина
    get_term_or_404(db, flashcard.term_id)
    # Убедимся, что для этого термина ещё нет карточки (уникальность term_id)
    existing = db.query(models.Flashcard).filter(models.Flashcard.term_id == flashcard.term_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Flashcard for this term already exists")
    db_flashcard = models.Flashcard(**flashcard.dict())
    db.add(db_flashcard)
    db.commit()
    db.refresh(db_flashcard)
    return db_flashcard

@flashcards_router.put("/{flashcard_id}", response_model=schemas.FlashcardOut)
def update_flashcard(
    flashcard_id: int,
    flashcard_update: schemas.FlashcardUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновить карточку."""
    db_flashcard = get_flashcard_or_404(db, flashcard_id)
    if flashcard_update.term_id is not None:
        # Проверяем новый term_id и уникальность
        get_term_or_404(db, flashcard_update.term_id)
        existing = db.query(models.Flashcard).filter(
            models.Flashcard.term_id == flashcard_update.term_id,
            models.Flashcard.id != flashcard_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Flashcard for this term already exists")
    for key, value in flashcard_update.dict(exclude_unset=True).items():
        setattr(db_flashcard, key, value)
    db.commit()
    db.refresh(db_flashcard)
    return db_flashcard

@flashcards_router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flashcard(
    flashcard_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удалить карточку."""
    db_flashcard = get_flashcard_or_404(db, flashcard_id)
    db.delete(db_flashcard)
    db.commit()
    return

# ---------- Quizzes ----------
@quizzes_router.get("/", response_model=List[schemas.QuizOut])
def list_quizzes(
    topic_id: Optional[int] = Query(None, description="Фильтр по теме"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить список квизов. Можно фильтровать по topic_id."""
    query = db.query(models.Quiz)
    if topic_id:
        query = query.filter(models.Quiz.topic_id == topic_id)
    return query.all()

@quizzes_router.post("/", response_model=schemas.QuizOut, status_code=status.HTTP_201_CREATED)
def create_quiz(
    quiz: schemas.QuizCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новый квиз."""
    # Проверка темы
    get_topic_or_404(db, quiz.topic_id)
    db_quiz = models.Quiz(**quiz.dict())
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

@quizzes_router.put("/{quiz_id}", response_model=schemas.QuizOut)
def update_quiz(
    quiz_id: int,
    quiz_update: schemas.QuizUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновить квиз."""
    db_quiz = get_quiz_or_404(db, quiz_id)
    if quiz_update.topic_id is not None:
        get_topic_or_404(db, quiz_update.topic_id)
    for key, value in quiz_update.dict(exclude_unset=True).items():
        setattr(db_quiz, key, value)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

@quizzes_router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удалить квиз (вопросы удалятся каскадно)."""
    db_quiz = get_quiz_or_404(db, quiz_id)
    db.delete(db_quiz)
    db.commit()
    return

# ---------- Questions ----------
@questions_router.get("/", response_model=List[schemas.QuestionOut])
def list_questions(
    quiz_id: Optional[int] = Query(None, description="Фильтр по квизу"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить список вопросов. Можно фильтровать по quiz_id."""
    query = db.query(models.Question)
    if quiz_id:
        query = query.filter(models.Question.quiz_id == quiz_id)
    return query.all()

@questions_router.post("/", response_model=schemas.QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новый вопрос."""
    # Проверка квиза
    get_quiz_or_404(db, question.quiz_id)
    db_question = models.Question(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@questions_router.put("/{question_id}", response_model=schemas.QuestionOut)
def update_question(
    question_id: int,
    question_update: schemas.QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновить вопрос."""
    db_question = get_question_or_404(db, question_id)
    if question_update.quiz_id is not None:
        get_quiz_or_404(db, question_update.quiz_id)
    for key, value in question_update.dict(exclude_unset=True).items():
        setattr(db_question, key, value)
    db.commit()
    db.refresh(db_question)
    return db_question

@questions_router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удалить вопрос."""
    db_question = get_question_or_404(db, question_id)
    db.delete(db_question)
    db.commit()
    return

# ---------- Объединение всех роутеров в один для удобного подключения ----------
content_router = APIRouter()
content_router.include_router(domains_router)
content_router.include_router(topics_router)
content_router.include_router(terms_router)
content_router.include_router(flashcards_router)
content_router.include_router(quizzes_router)
content_router.include_router(questions_router)