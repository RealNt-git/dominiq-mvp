# backend/app/api/ai_assistant.py
# API для AI-ассистента методолога
# Добавлено подробное логирование всех эндпоинтов

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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} uploading file: {file.filename}, domain: {domain}")

    if not (file.filename.endswith('.txt') or file.filename.endswith('.md')):
        logger.warning(f"Invalid file extension: {file.filename}")
        raise HTTPException(status_code=400, detail="Only .txt or .md files are allowed")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        logger.info(f"Temporary file created: {tmp_path}")

        logger.info("Calling document_processor.process_document...")
        doc_id = await document_processor.process_document(tmp_path, domain, file.filename)
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


@router.post("/drafts/approve", status_code=200)
def approve_drafts(
    request: schemas.DraftApproveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} approving drafts: doc_id={request.document_id}, draft_ids={request.draft_ids}")

    # Получаем черновики для утверждения
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

    # Создаём Quiz для документа
    quiz = None
    if doc:
        quiz = models.Quiz(
            title=f"Квиз по документу: {doc.filename}",
            topic_id=None
        )
        db.add(quiz)
        db.flush()
        logger.info(f"Created quiz for document {doc.id}: {quiz.title}")

    created_terms = []
    for draft in drafts:
        term = models.Term(
            term=draft.term,
            definition=draft.definition or "",
            example=draft.example,
            mnemonic=draft.mnemonic,
            image_url=None,
            domain_id=domain.id if domain else None,
            topic_id=None,
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

        if quiz:
            draft_questions = db.query(models.DraftQuiz).filter(
                models.DraftQuiz.document_id == draft.document_id,
                models.DraftQuiz.term_id == draft.id,
                models.DraftQuiz.status.in_(["new", "edited"])
            ).all()
            for dq in draft_questions:
                question = models.Question(
                    quiz_id=quiz.id,
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