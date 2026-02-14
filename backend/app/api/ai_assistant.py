# backend/app/api/ai_assistant.py
# API для AI-ассистента методолога (загрузка документов, черновики, утверждение)
# Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0
# Добавлен эндпоинт DELETE /drafts/{draft_id} для удаления черновика
# Добавлено получение domain_id из документа при утверждении

import tempfile
import shutil
import os
import json
import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app import models, schemas
from app.services import document_processor

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Assistant"])


@router.get("/documents", response_model=List[schemas.DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает список всех загруженных документов.
    """
    documents = db.query(models.Document).order_by(models.Document.uploaded_at.desc()).all()
    return documents


@router.post("/upload-document", response_model=schemas.DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Текстовый файл (.txt или .md)"),
    domain: str = Form(..., description="Предметная область (например, Ритейл)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Загружает текстовый документ, запускает его обработку (извлечение терминов,
    генерацию черновиков). Возвращает ID созданной записи Document.
    """
    # Проверка расширения
    if not (file.filename.endswith('.txt') or file.filename.endswith('.md')):
        raise HTTPException(status_code=400, detail="Only .txt or .md files are allowed")

    # Сохраняем загруженный файл во временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Запускаем обработку документа (асинхронно, внутри всё синхронно)
        doc_id = await document_processor.process_document(tmp_path, domain, file.filename)
        return {"document_id": doc_id, "message": "Документ загружен и обработан"}
    except Exception as e:
        # В случае ошибки удаляем временный файл и возвращаем ошибку
        logger.error(f"Error processing document: {e}", exc_info=True)  # <-- добавить эту строку
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        # Удаляем временный файл после обработки
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/drafts", response_model=List[schemas.DraftTermOut])
def list_drafts(
    document_id: Optional[int] = Query(None, description="Фильтр по документу"),
    status: Optional[str] = Query(None, description="Фильтр по статусу (new, edited, approved, rejected)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает список черновиков терминов с возможностью фильтрации.
    """
    query = db.query(models.DraftTerm)
    if document_id:
        query = query.filter(models.DraftTerm.document_id == document_id)
    if status:
        query = query.filter(models.DraftTerm.status == status)
    return query.all()


@router.put("/drafts/{draft_id}", response_model=schemas.DraftTermOut)
def update_draft(
    draft_id: int,
    draft_update: schemas.DraftTermUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Обновляет поля черновика термина (например, после ручной правки).
    """
    draft = db.query(models.DraftTerm).filter(models.DraftTerm.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft term not found")

    for key, value in draft_update.dict(exclude_unset=True).items():
        setattr(draft, key, value)
    draft.status = "edited"  # автоматически меняем статус
    db.commit()
    db.refresh(draft)
    return draft


@router.delete("/drafts/{draft_id}", status_code=204)
def delete_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Удаляет черновик термина.
    """
    draft = db.query(models.DraftTerm).filter(models.DraftTerm.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft term not found")
    db.delete(draft)
    db.commit()
    return


@router.post("/drafts/approve", status_code=200)
def approve_drafts(
    request: schemas.DraftApproveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Утверждает черновики: создаёт Term, Flashcard, Quiz и Questions.
    - Если передан document_id и не передан draft_ids, утверждаются все черновики документа.
    - Если передан список draft_ids, утверждаются только указанные черновики терминов.
    """
    # Получаем черновики для утверждения
    query = db.query(models.DraftTerm).filter(models.DraftTerm.status.in_(["new", "edited"]))
    if request.document_id:
        query = query.filter(models.DraftTerm.document_id == request.document_id)
    if request.draft_ids:
        query = query.filter(models.DraftTerm.id.in_(request.draft_ids))

    drafts = query.all()
    if not drafts:
        raise HTTPException(status_code=404, detail="No drafts found for approval")

    # Получаем документ (для названия квиза и домена)
    doc = None
    if request.document_id:
        doc = db.query(models.Document).filter(models.Document.id == request.document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

    # Находим домен по имени из документа
    domain = None
    if doc:
        domain = db.query(models.Domain).filter(models.Domain.name == doc.domain).first()
        if not domain:
            # Если домен не найден (например, пользователь ввел нестандартное имя), создаем его
            domain = models.Domain(name=doc.domain, description=f"Домен {doc.domain}")
            db.add(domain)
            db.flush()

    # Создаём Quiz для документа (если ещё не создан)
    quiz = None
    if doc:
        # Проверяем, нет ли уже квиза для этого документа (можно создать новый)
        quiz = models.Quiz(
            title=f"Квиз по документу: {doc.filename}",
            topic_id=None  # без темы, методолог потом привяжет
        )
        db.add(quiz)
        db.flush()

    # Для каждого черновика создаём Term и Flashcard
    for draft in drafts:
        # Создаём Term
        term = models.Term(
            term=draft.term,
            definition=draft.definition or "",
            example=draft.example,
            mnemonic=draft.mnemonic,  # сохраняем мнемонику, если есть
            image_url=None,
            domain_id=domain.id if domain else None,  # обязательно должен быть не NULL
            topic_id=None,
            source_document=doc.filename if doc else None,
            source_fragment=draft.context
        )
        db.add(term)
        db.flush()  # получаем id термина

        # Создаём Flashcard для термина
        flashcard = models.Flashcard(
            term_id=term.id,
            simplified_definition=draft.definition,
            hint=None
        )
        db.add(flashcard)

        # Если есть квиз, добавляем вопросы из DraftQuiz, связанные с этим черновиком
        if quiz:
            draft_questions = db.query(models.DraftQuiz).filter(
                models.DraftQuiz.document_id == draft.document_id,
                models.DraftQuiz.term_id == draft.id,  # term_id в DraftQuiz ссылается на DraftTerm.id
                models.DraftQuiz.status.in_(["new", "edited"])
            ).all()
            for dq in draft_questions:
                question = models.Question(
                    quiz_id=quiz.id,
                    text=dq.question,
                    type="single",  # пока только одиночный выбор
                    options=dq.options,
                    correct_answer=dq.correct,
                    explanation=dq.explanation
                )
                db.add(question)
                dq.status = "approved"  # помечаем как утверждённый

        # Помечаем черновик как утверждённый
        draft.status = "approved"

    db.commit()

    return {"message": f"Approved {len(drafts)} drafts, created quiz id {quiz.id if quiz else 'none'}"}


@router.get("/export/{document_id}")
def export_drafts(
    document_id: int,
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Экспортирует утверждённые черновики документа в JSON или CSV.
    Возвращает файл для скачивания.
    """
    # Получаем утверждённые черновики терминов
    drafts = db.query(models.DraftTerm).filter(
        models.DraftTerm.document_id == document_id,
        models.DraftTerm.status == "approved"
    ).all()

    if not drafts:
        raise HTTPException(status_code=404, detail="No approved drafts found for this document")

    # Преобразуем в список словарей
    data = []
    for d in drafts:
        data.append({
            "term": d.term,
            "definition": d.definition,
            "example": d.example,
            "context": d.context,
            "mnemonic": d.mnemonic  # добавляем мнемонику, если есть
        })

    if format == "json":
        content = json.dumps(data, ensure_ascii=False, indent=2)
        media_type = "application/json"
        filename = f"drafts_{document_id}.json"
    else:  # csv
        output = io.StringIO()
        # Обновляем поля для CSV
        writer = csv.DictWriter(output, fieldnames=["term", "definition", "example", "context", "mnemonic"])
        writer.writeheader()
        writer.writerows(data)
        content = output.getvalue()
        media_type = "text/csv"
        filename = f"drafts_{document_id}.csv"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )