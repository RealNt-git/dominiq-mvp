# backend/app/services/llm_orchestrator.py
import os
import logging
from typing import Optional, Dict, Any

from app.services.llm_client import LLMClient
from app.services.langflow_client import LangflowClient

logger = logging.getLogger(__name__)

# Глобальные экземпляры клиентов (инициализируются при первом обращении)
_llm_client: Optional[LLMClient] = None
_langflow_client: Optional[LangflowClient] = None

# Флаг использования Langflow (из переменной окружения)
USE_LANGFLOW = os.getenv("USE_LANGFLOW", "false").lower() == "true"

# ID flow для Langflow (должны быть заданы в окружении)
LANGFLOW_FLOW_VERIFY_TERM = os.getenv("LANGFLOW_FLOW_VERIFY_TERM")
LANGFLOW_FLOW_GENERATE_MNEMONIC = os.getenv("LANGFLOW_FLOW_GENERATE_MNEMONIC")
LANGFLOW_FLOW_GENERATE_QUESTIONS = os.getenv("LANGFLOW_FLOW_GENERATE_QUESTIONS")
LANGFLOW_FLOW_SUGGEST_TOPICS = os.getenv("LANGFLOW_FLOW_SUGGEST_TOPICS")
LANGFLOW_FLOW_GENERATE_TOPIC_CONTENT = os.getenv("LANGFLOW_FLOW_GENERATE_TOPIC_CONTENT")
LANGFLOW_FLOW_DESCRIBE_TOPIC = os.getenv("LANGFLOW_FLOW_DESCRIBE_TOPIC")

# --- Промпты для LLMClient (резервный вариант) ---

PROMPT_VERIFY_TERM = """
Является ли фраза "{candidate}" термином в области {domain}? Если да, найди в следующем контексте определение и пример использования.
Ответь строго в формате JSON с полями:
- is_term (bool)
- definition (str, если есть, иначе пустая строка)
- example (str, если есть, иначе пустая строка)

Контекст: "{context}"
"""

PROMPT_GENERATE_MNEMONIC = """
Придумай короткую мнемоническую фразу для запоминания термина '{term}' (определение: {definition}). Фраза должна быть на русском языке. Ответ дай одной строкой, без пояснений.
"""

PROMPT_GENERATE_QUESTIONS = """
Составь 2 вопроса с вариантами ответов (по 4 варианта) для проверки знания термина '{term}'.
Все тексты должны быть на русском языке (вопрос, варианты ответов, пояснение).
Определение: {definition}
Пример: {example}
Для каждого вопроса укажи правильный вариант (индекс 0-3).
Верни строго JSON-массив из 2 объектов с полями:
- question (str)
- options (list of 4 str)
- correct (int) - индекс правильного ответа
- explanation (str, пояснение, почему ответ правильный)
"""

PROMPT_SUGGEST_TOPICS = """
Ты — эксперт в области {domain}. Составь список из 3 самых популярных и важных тем для изучения {role}ом в этой области.
Для каждой темы напиши краткое описание (не более 500 символов) о том, что это, в каких бизнес-процессах применяется, приведи пример.
Ответ должен быть строго в формате JSON-массива объектов с полями:
- name (название темы)
- description (описание)

Пример формата:
[
  {{"name": "Управление запасами", "description": "..."}},
  {{"name": "Ценообразование в ритейле", "description": "..."}},
  ...
]
Только JSON, никаких пояснений.
"""

PROMPT_GENERATE_TOPIC_CONTENT = """
Ты — эксперт в области {domain}. Напиши подробную статью для аналитика на тему "{topic_name}".
Статья должна объяснять, что это такое, в каких бизнес-процессах применяется, привести примеры.
Объём — примерно 500-1000 символов. Текст должен быть на русском языке.
Не используй markdown, только обычный текст.
"""

PROMPT_DESCRIBE_TOPIC = """
Ты — эксперт в области {domain}. Напиши краткое описание (не более 500 символов) для темы "{topic_name}" для аналитика.
Опиши, что это такое, в каких бизнес-процессах применяется, приведи пример.
Твой ответ должен содержать только описание, без каких-либо дополнительных фраз, комментариев или повторения задания.
Начинай сразу с текста описания.
"""

# --- Инициализация клиентов ---

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
        logger.info("LLMClient initialized by orchestrator")
    return _llm_client

def get_langflow_client() -> LangflowClient:
    global _langflow_client
    if _langflow_client is None:
        _langflow_client = LangflowClient()
        logger.info("LangflowClient initialized by orchestrator")
    return _langflow_client

async def close_clients():
    """Закрывает всех клиентов (вызывается при завершении приложения)."""
    global _llm_client, _langflow_client
    if _llm_client:
        await _llm_client.close()
        _llm_client = None
    if _langflow_client:
        await _langflow_client.close()
        _langflow_client = None
    logger.info("All LLM clients closed")

# --- Основные функции оркестратора ---

async def verify_term(candidate: str, context: str, domain: str) -> str:
    """
    Проверяет, является ли кандидат термином.
    Возвращает сырой текст ответа (JSON).
    """
    if USE_LANGFLOW:
        flow_id = LANGFLOW_FLOW_VERIFY_TERM
        if not flow_id:
            raise ValueError("LANGFLOW_FLOW_VERIFY_TERM not set")
        client = get_langflow_client()
        inputs = {"candidate": candidate, "context": context, "domain": domain}
        logger.info(f"Using Langflow for verify_term with flow {flow_id}")
        return await client.run_flow(flow_id, inputs)
    else:
        prompt = PROMPT_VERIFY_TERM.format(candidate=candidate, context=context, domain=domain)
        client = get_llm_client()
        logger.info("Using LLMClient for verify_term")
        return await client.generate(prompt, max_tokens=300, temperature=0.1)

async def generate_mnemonic(term: str, definition: str) -> str:
    """Генерирует мнемонику для термина."""
    if USE_LANGFLOW:
        flow_id = LANGFLOW_FLOW_GENERATE_MNEMONIC
        if not flow_id:
            raise ValueError("LANGFLOW_FLOW_GENERATE_MNEMONIC not set")
        client = get_langflow_client()
        inputs = {"term": term, "definition": definition}
        logger.info(f"Using Langflow for generate_mnemonic with flow {flow_id}")
        return await client.run_flow(flow_id, inputs)
    else:
        prompt = PROMPT_GENERATE_MNEMONIC.format(term=term, definition=definition)
        client = get_llm_client()
        logger.info("Using LLMClient for generate_mnemonic")
        return await client.generate(prompt, max_tokens=50, temperature=0.5)

async def generate_questions(term: str, definition: str, example: str) -> str:
    """Генерирует вопросы для термина."""
    if USE_LANGFLOW:
        flow_id = LANGFLOW_FLOW_GENERATE_QUESTIONS
        if not flow_id:
            raise ValueError("LANGFLOW_FLOW_GENERATE_QUESTIONS not set")
        client = get_langflow_client()
        inputs = {"term": term, "definition": definition, "example": example}
        logger.info(f"Using Langflow for generate_questions with flow {flow_id}")
        return await client.run_flow(flow_id, inputs)
    else:
        prompt = PROMPT_GENERATE_QUESTIONS.format(term=term, definition=definition, example=example)
        client = get_llm_client()
        logger.info("Using LLMClient for generate_questions")
        return await client.generate(prompt, max_tokens=800, temperature=0.3)

async def suggest_topics(domain: str, role: str) -> str:
    """Предлагает темы для домена и роли."""
    if USE_LANGFLOW:
        flow_id = LANGFLOW_FLOW_SUGGEST_TOPICS
        if not flow_id:
            raise ValueError("LANGFLOW_FLOW_SUGGEST_TOPICS not set")
        client = get_langflow_client()
        inputs = {"domain": domain, "role": role}
        logger.info(f"Using Langflow for suggest_topics with flow {flow_id}")
        return await client.run_flow(flow_id, inputs)
    else:
        prompt = PROMPT_SUGGEST_TOPICS.format(domain=domain, role=role)
        client = get_llm_client()
        logger.info("Using LLMClient for suggest_topics")
        return await client.generate(prompt, max_tokens=1500, temperature=0.3)

async def generate_topic_content(domain: str, topic_name: str) -> str:
    """Генерирует статью по теме."""
    if USE_LANGFLOW:
        flow_id = LANGFLOW_FLOW_GENERATE_TOPIC_CONTENT
        if not flow_id:
            raise ValueError("LANGFLOW_FLOW_GENERATE_TOPIC_CONTENT not set")
        client = get_langflow_client()
        inputs = {"domain": domain, "topic_name": topic_name}
        logger.info(f"Using Langflow for generate_topic_content with flow {flow_id}")
        return await client.run_flow(flow_id, inputs)
    else:
        prompt = PROMPT_GENERATE_TOPIC_CONTENT.format(domain=domain, topic_name=topic_name)
        client = get_llm_client()
        logger.info("Using LLMClient for generate_topic_content")
        return await client.generate(prompt, max_tokens=1500, temperature=0.3)

async def describe_topic(domain: str, topic_name: str) -> str:
    """Генерирует описание темы."""
    if USE_LANGFLOW:
        flow_id = LANGFLOW_FLOW_DESCRIBE_TOPIC
        if not flow_id:
            raise ValueError("LANGFLOW_FLOW_DESCRIBE_TOPIC not set")
        client = get_langflow_client()
        inputs = {"domain": domain, "topic_name": topic_name}
        logger.info(f"Using Langflow for describe_topic with flow {flow_id}")
        return await client.run_flow(flow_id, inputs)
    else:
        prompt = PROMPT_DESCRIBE_TOPIC.format(domain=domain, topic_name=topic_name)
        client = get_llm_client()
        logger.info("Using LLMClient for describe_topic")
        return await client.generate(prompt, max_tokens=300, temperature=0.3)