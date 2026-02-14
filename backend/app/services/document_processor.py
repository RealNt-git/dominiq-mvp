# backend/app/services/document_processor.py
# Модуль обработки документов с подробнейшим логированием
# Исправлена ошибка бесконечного цикла в _split_into_chunks
# Исправлен импорт метрик для устранения циклической зависимости

import os
import re
import json
import logging
import time
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.services.llm_client import LLMClient
from app.services.term_extractor import extract_candidates
from app.database import SessionLocal
from app import models

# Импорт метрик из отдельного модуля (для предотвращения циклических импортов)
from app.core.metrics import document_processing_duration_seconds

logger = logging.getLogger(__name__)
logger.info("document_processor imported successfully")

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200
MAX_CANDIDATES = 10

async def process_document(file_path: str, domain: str, original_filename: str) -> int:
    start_time = time.time()
    logger.info(f"=== Starting process_document for file: {original_filename}, domain: {domain} ===")

    # 1. Чтение файла
    logger.info("Step 1: Reading file")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        full_text = f.read()
    if not full_text.strip():
        raise ValueError("Document is empty")
    logger.info(f"File read, size: {len(full_text)} characters")

    # 2. Сохранение документа в БД
    logger.info("Step 2: Saving document to DB")
    db = SessionLocal()
    try:
        doc = models.Document(
            filename=original_filename,
            domain=domain,
            content=full_text,
            processed=False
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_id = doc.id
        logger.info(f"Document saved to DB with id: {doc_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save document to DB: {e}")
        raise
    finally:
        db.close()
        logger.debug("DB session closed after save")

    # 3. Разбиение на чанки
    logger.info("Step 3: Splitting into chunks")
    chunk_start = time.time()
    chunks = _split_into_chunks(full_text, CHUNK_SIZE, CHUNK_OVERLAP)
    logger.info(f"Document split into {len(chunks)} chunks in {time.time()-chunk_start:.2f}s")

    # 4. Извлечение кандидатов
    logger.info("Step 4: Extracting candidates with YAKE")
    extract_start = time.time()
    candidates = extract_candidates(full_text, top_n=MAX_CANDIDATES, language="russian")
    logger.info(f"Extracted {len(candidates)} candidate terms in {time.time()-extract_start:.2f}s")

    # 5. Инициализация LLM клиента
    logger.info("Step 5: Initializing LLMClient")
    llm = LLMClient()
    logger.info("LLMClient initialized")

    # 6. Верификация кандидатов
    logger.info("Step 6: Verifying candidates")
    approved_terms = []
    try:
        for idx, cand in enumerate(candidates, 1):
            cand_start = time.time()
            logger.info(f"  Processing candidate {idx}/{len(candidates)}: '{cand}'")
            context = _find_context(full_text, cand)
            if not context:
                logger.debug(f"  No context found for '{cand}', skipping")
                continue
            term_data = await _verify_term(llm, cand, context, domain)
            if term_data:
                term_data["context"] = context
                term_data["document_id"] = doc_id
                approved_terms.append(term_data)
                logger.info(f"  Candidate '{cand}' APPROVED in {time.time()-cand_start:.2f}s")
            else:
                logger.info(f"  Candidate '{cand}' REJECTED in {time.time()-cand_start:.2f}s")
        logger.info(f"Verified {len(approved_terms)} terms, total verification time: {time.time()-extract_start:.2f}s")

        # 7. Сохранение черновиков
        logger.info("Step 7: Saving draft terms")
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
                logger.debug(f"Draft term saved with id {draft_term.id}")

                # 8. Генерация дополнительных материалов
                logger.info(f"Step 8: Generating additional materials for term '{term_info['term']}'")
                await _generate_additional_materials(llm, term_info, draft_term.id, doc_id, db)

            db.commit()
            logger.info(f"Drafts saved for document {doc_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving drafts: {e}")
            raise
        finally:
            db.close()
            logger.debug("DB session closed after saving drafts")

    finally:
        await llm.close()
        logger.debug("LLMClient closed")

    # 9. Помечаем документ как обработанный
    logger.info("Step 9: Marking document as processed")
    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if doc:
            doc.processed = True
            db.commit()
            logger.info(f"Document {doc_id} marked as processed")
    except Exception as e:
        logger.error(f"Failed to mark document as processed: {e}")
    finally:
        db.close()

    total_time = time.time() - start_time
    logger.info(f"=== process_document completed in {total_time:.2f}s, returning doc_id {doc_id} ===")

    # Отправляем метрику времени обработки в Prometheus
    document_processing_duration_seconds.observe(total_time)

    return doc_id


def _split_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Разбивает текст на перекрывающиеся чанки заданного размера (в символах)."""
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        # Если достигли конца текста, выходим
        if end == text_len:
            break
        start = end - overlap
        if start < 0:
            start = 0
    logger.info(f"Return {len(chunks)} chunks from _split_into_chunks")
    return chunks


def _find_context(text: str, term: str) -> Optional[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sent in sentences:
        if term.lower() in sent.lower():
            return sent.strip()
    return None


async def _verify_term(llm: LLMClient, candidate: str, context: str, domain: str) -> Optional[Dict[str, Any]]:
    prompt = f"""
Является ли фраза "{candidate}" термином в области {domain}? Если да, найди в следующем контексте определение и пример использования.
Ответь строго в формате JSON с полями:
- is_term (bool)
- definition (str, если есть, иначе пустая строка)
- example (str, если есть, иначе пустая строка)

Контекст: "{context}"
"""
    try:
        response = await llm.generate(prompt, max_tokens=300, temperature=0.1)
        logger.info(f"Raw response from LLM for '{candidate}': {response}")
        # Ищем JSON-объект в ответе (от первого '{' до последнего '}')
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end > start:
            json_str = response[start:end]
            data = json.loads(json_str)
            if data.get("is_term"):
                logger.info(f"Term verified: '{candidate}'")
                return {
                    "term": candidate,
                    "definition": data.get("definition", ""),
                    "example": data.get("example", "")
                }
            else:
                logger.info(f"Term rejected by LLM: '{candidate}'")
                return None
        else:
            logger.warning(f"Could not find JSON object in response for '{candidate}': {response[:200]}")
            return None
    except Exception as e:
        logger.warning(f"Error verifying term '{candidate}': {e}")
        return None


async def _generate_additional_materials(
    llm: LLMClient,
    term_info: Dict[str, Any],
    draft_term_id: int,
    document_id: int,
    db: Session
) -> None:
    term = term_info["term"]
    definition = term_info.get("definition", "")
    example = term_info.get("example", "")

    logger.info(f"Generating additional materials for term: '{term}'")

    # Мнемоника
    prompt_mnemonic = f"Придумай короткую мнемоническую фразу для запоминания термина '{term}' (определение: {definition}). Ответ дай одной строкой, без пояснений."
    try:
        mnemonic = await llm.generate(prompt_mnemonic, max_tokens=50, temperature=0.5)
        draft_term = db.query(models.DraftTerm).filter(models.DraftTerm.id == draft_term_id).first()
        if draft_term:
            draft_term.mnemonic = mnemonic
            logger.info(f"Mnemonic generated for '{term}': {mnemonic}")
        else:
            logger.warning(f"Draft term {draft_term_id} not found, cannot save mnemonic")
    except Exception as e:
        logger.warning(f"Failed to generate mnemonic for '{term}': {e}")

    # Вопросы
    prompt_quiz = f"""
Составь 2 вопроса с вариантами ответов (по 4 варианта) для проверки знания термина '{term}'.
Определение: {definition}
Пример: {example}
Для каждого вопроса укажи правильный вариант (индекс 0-3).
Верни строго JSON-массив из 2 объектов с полями:
- question (str)
- options (list of 4 str)
- correct (int) - индекс правильного ответа
- explanation (str, пояснение, почему ответ правильный)
"""
    try:
        response = await llm.generate(prompt_quiz, max_tokens=800, temperature=0.3)
        start = response.find("[")
        end = response.rfind("]") + 1
        if start != -1 and end > start:
            json_str = response[start:end]
            questions = json.loads(json_str)
            if isinstance(questions, list):
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
                logger.info(f"Generated {question_count} quiz questions for '{term}'")
            else:
                logger.warning(f"Quiz response is not a list for '{term}': {response[:200]}")
        else:
            logger.warning(f"Could not find JSON array in quiz response for '{term}': {response[:200]}")
    except Exception as e:
        logger.warning(f"Failed to generate quiz for '{term}': {e}")