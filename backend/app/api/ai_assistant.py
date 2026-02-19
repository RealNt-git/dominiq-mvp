# backend/app/api/ai_assistant.py
# API для AI-ассистента методолога
# Добавлено подробное логирование всех эндпоинтов
# Добавлены эндпоинты для работы с черновиками вопросов и получения терминов с вопросами
# Исправлено: upload_document теперь требует topic_id, approve_drafts использует тему документа

import tempfile
import shutil
import os
import json
import csv
import io
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app import models, schemas
from app.services import document_processor
from app.api.content import get_topic_or_404   # функция проверки темы

from app.services.topic_suggester import suggest_topics, generate_topic_content, describe_topic
from app.services.document_processor import process_document

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Assistant"])


@router.get("/documents", response_model=List[schemas.DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} requested document list")
    documents = db.query(models.Document).order_by(models.Document.uploaded_at.desc()).all()
    logger.info(f"Returning {len(documents)} documents")
    return documents


@router.post("/upload-document", response_model=schemas.DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Текстовый файл (.txt или .md)"),
    domain: str = Form(..., description="Предметная область (например, Ритейл)"),
    topic_id: int = Form(..., description="ID темы, к которой относится документ"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} uploading file: {file.filename}, domain: {domain}, topic_id: {topic_id}")

    if not (file.filename.endswith('.txt') or file.filename.endswith('.md')):
        logger.warning(f"Invalid file extension: {file.filename}")
        raise HTTPException(status_code=400, detail="Only .txt or .md files are allowed")

    # Проверяем существование темы
    topic = get_topic_or_404(db, topic_id)   # вызовет 404, если темы нет

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        logger.info(f"Temporary file created: {tmp_path}")

        logger.info("Calling document_processor.process_document...")
        # Передаём topic_id в процессор
        doc_id = await document_processor.process_document(tmp_path, domain, file.filename, topic_id)
        logger.info(f"Document processed successfully, doc_id: {doc_id}")
        return {"document_id": doc_id, "message": "Документ загружен и обработан"}
    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
            logger.debug(f"Temporary file deleted: {tmp_path}")


@router.get("/drafts", response_model=List[schemas.DraftTermOut])
def list_drafts(
    document_id: Optional[int] = Query(None, description="Фильтр по документу"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} requested drafts: doc_id={document_id}, status={status}")
    query = db.query(models.DraftTerm)
    if document_id:
        query = query.filter(models.DraftTerm.document_id == document_id)
    if status:
        query = query.filter(models.DraftTerm.status == status)
    drafts = query.all()
    logger.info(f"Returning {len(drafts)} drafts")
    return drafts


@router.get("/drafts/with-questions", response_model=List[schemas.DraftTermWithQuestions])
def list_drafts_with_questions(
    document_id: Optional[int] = Query(None, description="Фильтр по документу"),
    status: Optional[str] = Query(None, description="Фильтр по статусу (для терминов)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает список черновиков терминов, каждый с вложенными черновиками вопросов.
    """
    logger.info(f"User {current_user.email} requested drafts with questions: doc_id={document_id}, status={status}")
    query = db.query(models.DraftTerm)
    if document_id:
        query = query.filter(models.DraftTerm.document_id == document_id)
    if status:
        query = query.filter(models.DraftTerm.status == status)
    terms = query.all()
    result = []
    for term in terms:
        # Получаем вопросы для этого термина
        questions = db.query(models.DraftQuiz).filter(
            models.DraftQuiz.document_id == term.document_id,
            models.DraftQuiz.term_id == term.id
        ).all()
        # Преобразуем в схему DraftTermWithQuestions
        term_data = schemas.DraftTermOut.from_orm(term)
        questions_data = [schemas.DraftQuizOut.from_orm(q) for q in questions]
        # Создаём словарь для DraftTermWithQuestions
        term_with_questions = schemas.DraftTermWithQuestions(
            **term_data.dict(),
            questions=questions_data
        )
        result.append(term_with_questions)
    logger.info(f"Returning {len(result)} terms with questions")
    return result


@router.put("/drafts/{draft_id}", response_model=schemas.DraftTermOut)
def update_draft(
    draft_id: int,
    draft_update: schemas.DraftTermUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} updating draft {draft_id}")
    draft = db.query(models.DraftTerm).filter(models.DraftTerm.id == draft_id).first()
    if not draft:
        logger.warning(f"Draft {draft_id} not found")
        raise HTTPException(status_code=404, detail="Draft term not found")
    for key, value in draft_update.dict(exclude_unset=True).items():
        setattr(draft, key, value)
    draft.status = "edited"
    db.commit()
    db.refresh(draft)
    logger.info(f"Draft {draft_id} updated")
    return draft


@router.delete("/drafts/{draft_id}", status_code=204)
def delete_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} deleting draft {draft_id}")
    draft = db.query(models.DraftTerm).filter(models.DraftTerm.id == draft_id).first()
    if not draft:
        logger.warning(f"Draft {draft_id} not found")
        raise HTTPException(status_code=404, detail="Draft term not found")
    db.delete(draft)
    db.commit()
    logger.info(f"Draft {draft_id} deleted")
    return


# ---------- Эндпоинты для черновиков вопросов ----------

@router.get("/draft-questions", response_model=List[schemas.DraftQuizOut])
def list_draft_questions(
    document_id: Optional[int] = Query(None, description="Фильтр по документу"),
    term_id: Optional[int] = Query(None, description="Фильтр по термину"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} requested draft questions: doc_id={document_id}, term_id={term_id}, status={status}")
    query = db.query(models.DraftQuiz)
    if document_id:
        query = query.filter(models.DraftQuiz.document_id == document_id)
    if term_id:
        query = query.filter(models.DraftQuiz.term_id == term_id)
    if status:
        query = query.filter(models.DraftQuiz.status == status)
    questions = query.all()
    logger.info(f"Returning {len(questions)} draft questions")
    return questions


@router.put("/draft-questions/{question_id}", response_model=schemas.DraftQuizOut)
def update_draft_question(
    question_id: int,
    question_update: schemas.DraftQuizUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} updating draft question {question_id}")
    question = db.query(models.DraftQuiz).filter(models.DraftQuiz.id == question_id).first()
    if not question:
        logger.warning(f"Draft question {question_id} not found")
        raise HTTPException(status_code=404, detail="Draft question not found")
    for key, value in question_update.dict(exclude_unset=True).items():
        setattr(question, key, value)
    question.status = "edited"
    db.commit()
    db.refresh(question)
    logger.info(f"Draft question {question_id} updated")
    return question


@router.delete("/draft-questions/{question_id}", status_code=204)
def delete_draft_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} deleting draft question {question_id}")
    question = db.query(models.DraftQuiz).filter(models.DraftQuiz.id == question_id).first()
    if not question:
        logger.warning(f"Draft question {question_id} not found")
        raise HTTPException(status_code=404, detail="Draft question not found")
    db.delete(question)
    db.commit()
    logger.info(f"Draft question {question_id} deleted")
    return


@router.post("/drafts/approve", status_code=200)
def approve_drafts(
    request: schemas.DraftApproveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} approving drafts: doc_id={request.document_id}, draft_ids={request.draft_ids}")

    # Получаем черновики терминов для утверждения
    query = db.query(models.DraftTerm).filter(models.DraftTerm.status.in_(["new", "edited"]))
    if request.document_id:
        query = query.filter(models.DraftTerm.document_id == request.document_id)
    if request.draft_ids:
        query = query.filter(models.DraftTerm.id.in_(request.draft_ids))

    drafts = query.all()
    if not drafts:
        logger.warning("No drafts found for approval")
        raise HTTPException(status_code=404, detail="No drafts found for approval")

    # Получаем документ
    doc = None
    if request.document_id:
        doc = db.query(models.Document).filter(models.Document.id == request.document_id).first()
        if not doc:
            logger.warning(f"Document {request.document_id} not found")
            raise HTTPException(status_code=404, detail="Document not found")

    # Находим или создаём домен
    domain = None
    if doc:
        domain = db.query(models.Domain).filter(models.Domain.name == doc.domain).first()
        if not domain:
            domain = models.Domain(name=doc.domain, description=f"Домен {doc.domain}")
            db.add(domain)
            db.flush()
            logger.info(f"Created new domain: {doc.domain}")

    # Создаём Quiz для документа, привязывая к теме документа
    quiz = None
    if doc:
        quiz = models.Quiz(
            title=f"Квиз по документу: {doc.filename}",
            topic_id=doc.topic_id   # используем тему документа
        )
        db.add(quiz)
        db.flush()
        logger.info(f"Created quiz for document {doc.id}: {quiz.title} (topic_id={quiz.topic_id})")

    created_terms = []
    for draft in drafts:
        term = models.Term(
            term=draft.term,
            definition=draft.definition or "",
            example=draft.example,
            mnemonic=draft.mnemonic,
            image_url=None,
            domain_id=domain.id if domain else None,
            topic_id=doc.topic_id if doc else None,  # можно также привязать термины к теме документа (опционально)
            source_document=doc.filename if doc else None,
            source_fragment=draft.context
        )
        db.add(term)
        db.flush()
        created_terms.append(term.id)

        flashcard = models.Flashcard(
            term_id=term.id,
            simplified_definition=draft.definition,
            hint=None
        )
        db.add(flashcard)

        # Обрабатываем вопросы, связанные с этим черновиком термина
        if quiz:
            draft_questions = db.query(models.DraftQuiz).filter(
                models.DraftQuiz.document_id == draft.document_id,
                models.DraftQuiz.term_id == draft.id,
                models.DraftQuiz.status.in_(["new", "edited"])
            ).all()
            for dq in draft_questions:
                question = models.Question(
                    quiz_id=quiz.id,
                    term_id=term.id,
                    text=dq.question,
                    type="single",
                    options=dq.options,
                    correct_answer=dq.correct,
                    explanation=dq.explanation
                )
                db.add(question)
                dq.status = "approved"
            logger.debug(f"Added {len(draft_questions)} questions for draft {draft.id}")

        draft.status = "approved"

    db.commit()
    logger.info(f"Approved {len(drafts)} drafts, created terms: {created_terms}, quiz id: {quiz.id if quiz else 'none'}")
    return {"message": f"Approved {len(drafts)} drafts, created quiz id {quiz.id if quiz else 'none'}"}

# ---------- Эндпоинты для подбора тем ----------

@router.post("/topics/suggest", response_model=schemas.TopicSuggestionResponse)
async def suggest_topics_endpoint(
    request: schemas.TopicSuggestionRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Подбирает 3 популярные темы для заданного домена и роли.
    """
    logger.info("Topic suggestion requested", extra={
        "user_email": current_user.email,
        "domain": request.domain,
        "role": request.role
    })
    try:
        topics = await suggest_topics(request.domain, request.role)
        if not topics:
            raise HTTPException(status_code=500, detail="Не удалось получить темы от AI")
        return {"topics": topics}
    except Exception as e:
        logger.error("Topic suggestion failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Ошибка при подборе тем")


@router.post("/topics/generate-content", response_model=schemas.TopicContentGenerationResponse)
async def generate_topics_content(
    request: schemas.TopicContentGenerationRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Генерирует статьи для списка тем.
    """
    logger.info("Topic content generation requested", extra={
        "user_email": current_user.email,
        "domain": request.domain,
        "topics_count": len(request.topics)
    })
    try:
        items = []
        for topic_name in request.topics:
            content = await generate_topic_content(request.domain, topic_name)
            items.append({"name": topic_name, "content": content})
        return {"items": items}
    except Exception as e:
        logger.error("Topic content generation failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Ошибка при генерации контента")


@router.post("/topics/approve", status_code=200)
async def approve_topics(
    request: schemas.TopicApproveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Принимает список тем с контентом, создаёт темы (если их нет) и запускает обработку каждой темы
    как документа для генерации терминов, карточек и квизов.
    """
    logger.info("Topic approval requested", extra={
        "user_email": current_user.email,
        "domain": request.domain,
        "topics_count": len(request.topics)
    })

    # Получаем или создаём домен
    domain_obj = db.query(models.Domain).filter(models.Domain.name == request.domain).first()
    if not domain_obj:
        domain_obj = models.Domain(name=request.domain, description=f"Домен {request.domain}")
        db.add(domain_obj)
        db.flush()
        logger.info(f"Created new domain: {request.domain}")

    # Словарь для хранения созданных/найденных тем
    topics_map = {}

    # Первый проход: создаём или получаем все темы
    for item in request.topics:
        topic = db.query(models.Topic).filter(
            models.Topic.domain_id == domain_obj.id,
            models.Topic.name == item.name
        ).first()
        if not topic:
            topic = models.Topic(
                name=item.name,
                description=f"Тема, сгенерированная AI для домена {request.domain}",
                domain_id=domain_obj.id
            )
            db.add(topic)
            db.flush()
            logger.info(f"Created new topic: {item.name} (id={topic.id})")
        else:
            logger.info(f"Topic already exists: {item.name} (id={topic.id})")
        topics_map[item.name] = topic

    # Фиксируем все темы в БД
    db.commit()

    created_topic_ids = []
    for item in request.topics:
        topic = topics_map[item.name]

        # Сохраняем контент во временный файл и запускаем обработку
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp.write(item.content)
            tmp_path = tmp.name

        try:
            doc_id = await process_document(
                file_path=tmp_path,
                domain=request.domain,
                original_filename=f"{item.name}.txt",
                topic_id=topic.id
            )
            created_topic_ids.append({"topic_id": topic.id, "document_id": doc_id})
        except Exception as e:
            logger.error(f"Failed to process topic '{item.name}'", exc_info=True, extra={"error": str(e)})
            raise HTTPException(status_code=500, detail=f"Ошибка обработки темы {item.name}")
        finally:
            os.unlink(tmp_path)

    logger.info(f"Successfully processed {len(created_topic_ids)} topics")
    return {"message": f"Обработано {len(created_topic_ids)} тем", "details": created_topic_ids}


# ---------- Эндпоинты для управления сессиями подбора тем ----------

@router.post("/topics/sessions", response_model=schemas.TopicGenerationSessionOut, status_code=201)
def create_topic_session(
    session_data: schemas.TopicGenerationSessionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создаёт новую сессию подбора тем."""
    logger.info("Creating topic generation session", extra={
        "user_email": current_user.email,
        "domain": session_data.domain
    })
    db_session = models.TopicGenerationSession(
        user_id=current_user.id,
        **session_data.dict()
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    logger.info("Topic session created", extra={"session_id": db_session.id})
    return db_session


@router.get("/topics/sessions", response_model=List[schemas.TopicGenerationSessionOut])
def list_topic_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Возвращает все сессии текущего пользователя."""
    logger.info("Listing topic sessions", extra={"user_email": current_user.email})
    sessions = db.query(models.TopicGenerationSession).filter(
        models.TopicGenerationSession.user_id == current_user.id
    ).order_by(models.TopicGenerationSession.updated_at.desc()).all()
    logger.info(f"Found {len(sessions)} sessions")
    return sessions


@router.get("/topics/sessions/{session_id}", response_model=schemas.TopicGenerationSessionOut)
def get_topic_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Возвращает сессию по ID."""
    session = db.query(models.TopicGenerationSession).filter(
        models.TopicGenerationSession.id == session_id,
        models.TopicGenerationSession.user_id == current_user.id
    ).first()
    if not session:
        logger.warning(f"Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/topics/sessions/{session_id}", response_model=schemas.TopicGenerationSessionOut)
def update_topic_session(
    session_id: int,
    session_update: schemas.TopicGenerationSessionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновляет сессию."""
    session = db.query(models.TopicGenerationSession).filter(
        models.TopicGenerationSession.id == session_id,
        models.TopicGenerationSession.user_id == current_user.id
    ).first()
    if not session:
        logger.warning(f"Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")
    for key, value in session_update.dict(exclude_unset=True).items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    logger.info(f"Session {session_id} updated")
    return session


@router.delete("/topics/sessions/{session_id}", status_code=204)
def delete_topic_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удаляет сессию."""
    session = db.query(models.TopicGenerationSession).filter(
        models.TopicGenerationSession.id == session_id,
        models.TopicGenerationSession.user_id == current_user.id
    ).first()
    if not session:
        logger.warning(f"Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    logger.info(f"Session {session_id} deleted")
    return

@router.get("/export/{document_id}")
def export_drafts(
    document_id: int,
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} exporting drafts for doc {document_id} as {format}")
    drafts = db.query(models.DraftTerm).filter(
        models.DraftTerm.document_id == document_id,
        models.DraftTerm.status == "approved"
    ).all()
    if not drafts:
        logger.warning(f"No approved drafts for document {document_id}")
        raise HTTPException(status_code=404, detail="No approved drafts found for this document")

    data = [{
        "term": d.term,
        "definition": d.definition,
        "example": d.example,
        "context": d.context,
        "mnemonic": d.mnemonic
    } for d in drafts]

    if format == "json":
        content = json.dumps(data, ensure_ascii=False, indent=2)
        media_type = "application/json"
        filename = f"drafts_{document_id}.json"
    else:  # csv
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["term", "definition", "example", "context", "mnemonic"])
        writer.writeheader()
        writer.writerows(data)
        content = output.getvalue()
        media_type = "text/csv"
        filename = f"drafts_{document_id}.csv"

    logger.info(f"Export completed, {len(drafts)} records")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/topics/describe", response_model=schemas.SuggestedTopic)
async def describe_topic_endpoint(
    request: schemas.TopicDescribeRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Генерирует описание для указанной темы.
    """
    logger.info("Topic description requested", extra={
        "user_email": current_user.email,
        "domain": request.domain,
        "topic_name": request.topic_name
    })
    try:
        description = await describe_topic(request.domain, request.topic_name)
        return {"name": request.topic_name, "description": description}
    except Exception as e:
        logger.error("Topic description failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Ошибка при генерации описания")