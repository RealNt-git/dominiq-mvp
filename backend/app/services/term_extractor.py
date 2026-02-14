# backend/app/services/term_extractor.py
# Модуль быстрого извлечения кандидатов в термины с помощью YAKE и KeyBERT
# Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

import logging
from typing import List, Optional

# Библиотеки для извлечения ключевых слов
import yake
from keybert import KeyBERT

# Для работы со стоп-словами (может потребоваться загрузка)
import nltk
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

# Глобальные переменные для кэширования загрузок
_nltk_ready = False
_kw_model = None


def _ensure_nltk_stopwords():
    """
    Загружает русские стоп-слова из nltk, если они ещё не загружены.
    Вызывается при первом обращении.
    """
    global _nltk_ready
    if not _nltk_ready:
        try:
            nltk.data.find('corpora/stopwords.zip')
        except LookupError:
            nltk.download('stopwords', quiet=True)
        _nltk_ready = True


def _get_keybert_model():
    """Ленивая инициализация модели KeyBERT (одна на все вызовы)."""
    global _kw_model
    if _kw_model is None:
        _kw_model = KeyBERT()
    return _kw_model


def extract_candidates(text: str, top_n: int = 30, language: str = "russian") -> List[str]:
    """
    Извлекает кандидатов в термины из текста, комбинируя YAKE и KeyBERT.

    Аргументы:
        text (str): исходный текст (желательно не слишком короткий)
        top_n (int): максимальное количество кандидатов от каждого алгоритма
        language (str): язык текста ('russian' или 'english' и т.д.)

    Возвращает:
        List[str]: список уникальных кандидатов (в оригинальном регистре, без дубликатов).
    """
    if not text or not text.strip():
        return []

    # 1. YAKE
    try:
        # Настройка YAKE: язык, максимальное количество слов в фразе (n=2),
        # количество кандидатов (top=top_n)
        yake_extractor = yake.KeywordExtractor(
            lan=language,
            n=2,
            top=top_n,
            features=None
        )
        yake_keywords = [kw for kw, score in yake_extractor.extract_keywords(text)]
    except Exception as e:
        logger.error(f"YAKE extraction failed: {e}")
        yake_keywords = []

    # 2. KeyBERT
    try:
        # Загружаем стоп-слова для указанного языка (если есть в nltk)
        _ensure_nltk_stopwords()
        # Для русского языка stopwords.words('russian'), иначе пустой список
        if language == "russian":
            stop_words = stopwords.words('russian')
        else:
            stop_words = []

        kw_model = _get_keybert_model()
        # KeyBERT возвращает список кортежей (слово, релевантность)
        keybert_keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words=stop_words,
            top_n=top_n
        )
        keybert_keywords = [kw for kw, score in keybert_keywords]
    except Exception as e:
        logger.error(f"KeyBERT extraction failed: {e}")
        keybert_keywords = []

    # Объединение и дедупликация с учётом регистра (сравниваем в нижнем регистре)
    seen = set()
    candidates = []
    for kw in yake_keywords + keybert_keywords:
        normalized = kw.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            candidates.append(kw.strip())  # сохраняем оригинальное написание

    logger.debug(f"Extracted {len(candidates)} unique term candidates")
    return candidates