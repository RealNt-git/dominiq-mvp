# backend/app/services/document_processor.py
# Модуль обработки документов с подробнейшим логированием (включая структурированные логи для Kibana)
# Исправлено: удалены прямые вызовы LLMClient, всё через оркестратор

import os
import re
import json
import logging
import time
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.services import llm_orchestrator  # оркестратор для всех LLM-вызовов
from app.services.term_extractor import extract_candidates
from app.database import SessionLocal
from app import models

from app.core.metrics import document_processing_duration_seconds

logger = logging.getLogger(__name__)

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200
MAX_CANDIDATES = 30

async def process_document(file_path: str, domain: str, original_filename: str, topic_id: int) -> int:
    start_time = time.time()
    logger.info("Starting document processing", extra={
        "action": "process_document",
        "file_name": original_filename,
        "domain": domain,
        "topic_id": topic_id,
        "event": "start"
    })

    # 1. Чтение файла
    if not os.path.exists(file_path):
        logger.error("File not found", extra={
            "action": "process_document",
            "file_path": file_path,
            "error": "FileNotFound"
        })
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        full_text = f.read()
    if not full_text.strip():
        logger.error("Document empty", extra={
            "action": "process_document",
            "file_name": original_filename
        })
        raise ValueError("Document is empty")
    logger.info("File read", extra={
        "action": "process_document",
        "file_name": original_filename,
        "size_chars": len(full_text),
        "event": "file_read"
    })

    # 2. Сохранение документа в БД
    db = SessionLocal()
    try:
        doc = models.Document(
            filename=original_filename,
            domain=domain,
            topic_id=topic_id,
            content=full_text,
            processed=False
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_id = doc.id
        logger.info("Document saved to DB", extra={
            "action": "process_document",
            "document_id": doc_id,
            "topic_id": doc.topic_id,
            "event": "db_save"
        })
    except Exception as e:
        db.rollback()
        logger.error("Failed to save document to DB", exc_info=True, extra={
            "action": "process_document",
            "error": str(e)
        })
        raise
    finally:
        db.close()

    # 3. Разбиение на чанки (не используется напрямую, но оставим для логов)
    chunk_start = time.time()
    chunks = _split_into_chunks(full_text, CHUNK_SIZE, CHUNK_OVERLAP)
    logger.info("Document split into chunks", extra={
        "action": "process_document",
        "document_id": doc_id,
        "chunks_count": len(chunks),
        "duration_sec": round(time.time() - chunk_start, 3)
    })

    # 4. Извлечение кандидатов
    extract_start = time.time()
    candidates = extract_candidates(full_text, top_n=MAX_CANDIDATES, language="russian")
    logger.info("Candidates extracted", extra={
        "action": "process_document",
        "document_id": doc_id,
        "candidates_count": len(candidates),
        "duration_sec": round(time.time() - extract_start, 3)
    })

    # 5. Верификация кандидатов
    approved_terms = []
    verification_start = time.time()

    for idx, cand in enumerate(candidates, 1):
        cand_start = time.time()
        logger.info("Processing candidate", extra={
            "action": "verify_candidate",
            "document_id": doc_id,
            "candidate_index": idx,
            "candidate_text": cand,
            "event": "start"
        })
        context = _find_context(full_text, cand)
        if not context:
            logger.debug("No context found for candidate", extra={
                "action": "verify_candidate",
                "document_id": doc_id,
                "candidate": cand
            })
            continue

        try:
            response = await llm_orchestrator.verify_term(cand, context, domain)
            # Парсим JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                if data.get("is_term"):
                    term_data = {
                        "term": cand,
                        "definition": data.get("definition", ""),
                        "example": data.get("example", ""),
                        "context": context,
                        "document_id": doc_id
                    }
                    approved_terms.append(term_data)
                    logger.info("Candidate approved", extra={
                        "action": "verify_candidate",
                        "document_id": doc_id,
                        "candidate": cand,
                        "duration_sec": round(time.time() - cand_start, 3),
                        "event": "approved"
                    })
                else:
                    logger.info("Candidate rejected", extra={
                        "action": "verify_candidate",
                        "document_id": doc_id,
                        "candidate": cand,
                        "duration_sec": round(time.time() - cand_start, 3),
                        "event": "rejected"
                    })
            else:
                logger.warning("Could not parse JSON from LLM response", extra={
                    "action": "verify_candidate",
                    "document_id": doc_id,
                    "candidate": cand,
                    "response_preview": response[:200]
                })
        except Exception as e:
            logger.error(f"Error verifying term: {e}", exc_info=True, extra={
                "action": "verify_candidate",
                "document_id": doc_id,
                "candidate": cand
            })
            # продолжаем со следующим кандидатом

    logger.info("Verification completed", extra={
        "action": "process_document",
        "document_id": doc_id,
        "approved_count": len(approved_terms),
        "total_candidates": len(candidates),
        "duration_sec": round(time.time() - verification_start, 3)
    })

    # 6. Сохранение черновиков и генерация доп. материалов
    if approved_terms:
        db = SessionLocal()
        try:
            for term_info in approved_terms:
                draft_term = models.DraftTerm(
                    document_id=term_info["document_id"],
                    term=term_info["term"],
                    definition=term_info.get("definition", ""),
                    example=term_info.get("example", ""),
                    context=term_info.get("context", ""),
                    status="new"
                )
                db.add(draft_term)
                db.flush()
                logger.debug("Draft term saved", extra={
                    "action": "save_draft",
                    "document_id": doc_id,
                    "draft_term_id": draft_term.id,
                    "term": term_info["term"]
                })

                # Генерация дополнительных материалов (мнемоника, вопросы)
                await _generate_additional_materials(term_info, draft_term.id, doc_id, db)

            db.commit()
            logger.info("Drafts saved", extra={
                "action": "process_document",
                "document_id": doc_id,
                "drafts_saved": len(approved_terms)
            })
        except Exception as e:
            db.rollback()
            logger.error("Error saving drafts", exc_info=True, extra={
                "action": "process_document",
                "document_id": doc_id,
                "error": str(e)
            })
            raise
        finally:
            db.close()
    else:
        logger.info("No approved terms, skipping draft creation", extra={
            "action": "process_document",
            "document_id": doc_id
        })

    # 7. Помечаем документ как обработанный
    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if doc:
            doc.processed = True
            db.commit()
            logger.info("Document marked as processed", extra={
                "action": "process_document",
                "document_id": doc_id
            })
    except Exception as e:
        logger.error("Failed to mark document as processed", exc_info=True, extra={
            "action": "process_document",
            "document_id": doc_id,
            "error": str(e)
        })
    finally:
        db.close()

    total_time = time.time() - start_time
    logger.info("Document processing completed", extra={
        "action": "process_document",
        "document_id": doc_id,
        "total_duration_sec": round(total_time, 3),
        "approved_terms": len(approved_terms),
        "event": "end"
    })

    document_processing_duration_seconds.observe(total_time)
    return doc_id


# ---------- Вспомогательные функции ----------

def _split_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        if end == text_len:
            break
        start = end - overlap
        if start < 0:
            start = 0
    logger.info("Chunks created", extra={
        "action": "_split_into_chunks",
        "chunk_size": chunk_size,
        "overlap": overlap,
        "chunks_count": len(chunks)
    })
    return chunks


def _find_context(text: str, term: str) -> Optional[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sent in sentences:
        if term.lower() in sent.lower():
            logger.debug("Context found for term", extra={
                "action": "_find_context",
                "term": term,
                "context_snippet": sent[:100] + "..." if len(sent) > 100 else sent
            })
            return sent.strip()
    logger.debug("No context found for term", extra={
        "action": "_find_context",
        "term": term
    })
    return None


async def _generate_additional_materials(
    term_info: Dict[str, Any],
    draft_term_id: int,
    document_id: int,
    db: Session
) -> None:
    """Генерирует мнемонику и вопросы для термина через оркестратор."""
    term = term_info["term"]
    definition = term_info.get("definition", "")
    example = term_info.get("example", "")

    logger.info("Generating additional materials for term", extra={
        "action": "generate_additional_materials",
        "document_id": document_id,
        "draft_term_id": draft_term_id,
        "term": term,
        "event": "start"
    })

    # Мнемоника
    try:
        mnemonic = await llm_orchestrator.generate_mnemonic(term, definition)
        draft_term = db.query(models.DraftTerm).filter(models.DraftTerm.id == draft_term_id).first()
        if draft_term:
            draft_term.mnemonic = mnemonic
            logger.info("Mnemonic generated", extra={
                "action": "generate_additional_materials",
                "document_id": document_id,
                "draft_term_id": draft_term_id,
                "term": term,
                "mnemonic": mnemonic
            })
        else:
            logger.warning("Draft term not found for mnemonic", extra={
                "action": "generate_additional_materials",
                "document_id": document_id,
                "draft_term_id": draft_term_id
            })
    except Exception as e:
        logger.error("Failed to generate mnemonic", exc_info=True, extra={
            "action": "generate_additional_materials",
            "document_id": document_id,
            "draft_term_id": draft_term_id,
            "term": term,
            "error": str(e)
        })

    # Вопросы
    try:
        response = await llm_orchestrator.generate_questions(term, definition, example)

        # Парсинг JSON-массива
        start = response.find('[')
        end = response.rfind(']') + 1
        questions = None
        if start != -1 and end > start:
            try:
                questions = json.loads(response[start:end])
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON array", extra={
                    "action": "generate_additional_materials",
                    "document_id": document_id,
                    "draft_term_id": draft_term_id,
                    "term": term,
                    "response_preview": response[:200]
                })

        # Если не массив, пробуем одиночный объект
        if questions is None:
            start_obj = response.find('{')
            end_obj = response.rfind('}') + 1
            if start_obj != -1 and end_obj > start_obj:
                try:
                    single_q = json.loads(response[start_obj:end_obj])
                    if isinstance(single_q, dict) and all(k in single_q for k in ("question", "options", "correct")):
                        questions = [single_q]
                        logger.info("Parsed single question object", extra={"term": term})
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON object", extra={"term": term})

        if questions and isinstance(questions, list):
            question_count = 0
            for q in questions:
                if all(k in q for k in ("question", "options", "correct")):
                    draft_quiz = models.DraftQuiz(
                        document_id=document_id,
                        term_id=draft_term_id,
                        question=q["question"],
                        options=q["options"],
                        correct=q["correct"],
                        explanation=q.get("explanation", ""),
                        status="new"
                    )
                    db.add(draft_quiz)
                    question_count += 1
            logger.info(f"Generated {question_count} quiz questions", extra={
                "action": "generate_additional_materials",
                "document_id": document_id,
                "draft_term_id": draft_term_id,
                "term": term,
                "questions_count": question_count
            })
        else:
            logger.warning("Could not parse questions", extra={
                "action": "generate_additional_materials",
                "document_id": document_id,
                "draft_term_id": draft_term_id,
                "term": term
            })
    except Exception as e:
        logger.error("Failed to generate quiz", exc_info=True, extra={
            "action": "generate_additional_materials",
            "document_id": document_id,
            "draft_term_id": draft_term_id,
            "term": term,
            "error": str(e)
        })