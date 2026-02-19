# backend/app/services/term_extractor.py
# Модуль быстрого извлечения кандидатов в термины (только YAKE) с логированием

import logging
from typing import List
import yake

logger = logging.getLogger(__name__)

def extract_candidates(text: str, top_n: int = 30, language: str = "russian") -> List[str]:
    """
    Извлекает кандидатов в термины из текста с помощью YAKE.
    """
    if not text or not text.strip():
        logger.info("Empty text provided to extract_candidates", extra={
            "action": "extract_candidates",
            "text_length": 0,
            "event": "empty"
        })
        return []

    try:
        yake_extractor = yake.KeywordExtractor(lan=language, n=2, top=top_n, features=None)
        keywords = [kw for kw, score in yake_extractor.extract_keywords(text)]
        logger.info("YAKE extraction completed", extra={
            "action": "extract_candidates",
            "language": language,
            "top_n": top_n,
            "candidates_count": len(keywords),
            "event": "success"
        })
        return keywords
    except Exception as e:
        logger.error("YAKE extraction failed", extra={
            "action": "extract_candidates",
            "language": language,
            "top_n": top_n,
            "error": str(e),
            "exc_info": True
        })
        return []