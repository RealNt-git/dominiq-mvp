# backend/app/services/term_extractor.py
# Модуль быстрого извлечения кандидатов в термины (только YAKE)

import logging
from typing import List
import yake

logger = logging.getLogger(__name__)

def extract_candidates(text: str, top_n: int = 30, language: str = "russian") -> List[str]:
    """
    Извлекает кандидатов в термины из текста с помощью YAKE.
    """
    if not text or not text.strip():
        logger.debug("Empty text, returning empty list")
        return []

    try:
        yake_extractor = yake.KeywordExtractor(lan=language, n=2, top=top_n, features=None)
        keywords = [kw for kw, score in yake_extractor.extract_keywords(text)]
        logger.debug(f"YAKE extracted {len(keywords)} keywords")
        return keywords
    except Exception as e:
        logger.error(f"YAKE extraction failed: {e}")
        return []