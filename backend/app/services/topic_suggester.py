# backend/app/services/topic_suggester.py
import json
import logging
import time  # добавлен импорт time
from typing import List, Dict, Any

from app.services import llm_orchestrator  # новый импорт

logger = logging.getLogger(__name__)

async def suggest_topics(domain: str, role: str = "аналитик") -> List[Dict[str, str]]:
    try:
        response = await llm_orchestrator.suggest_topics(domain, role)
        # Парсинг JSON (как раньше)
        start = response.find('[')
        end = response.rfind(']') + 1
        if start != -1 and end > start:
            topics = json.loads(response[start:end])
            if isinstance(topics, list):
                validated = []
                for t in topics:
                    if isinstance(t, dict) and "name" in t and "description" in t:
                        validated.append({"name": t["name"], "description": t["description"]})
                return validated
        return []
    except Exception as e:
        logger.error(f"Error suggesting topics: {e}")
        return []


async def generate_topic_content(domain: str, topic_name: str) -> str:
    try:
        return await llm_orchestrator.generate_topic_content(domain, topic_name)
    except Exception as e:
        logger.error(f"Error generating topic content: {e}")
        return f"Ошибка генерации контента для темы {topic_name}"

async def describe_topic(domain: str, topic_name: str) -> str:
    try:
        return await llm_orchestrator.describe_topic(domain, topic_name)
    except Exception as e:
        logger.error(f"Error describing topic: {e}")
        return f"Не удалось сгенерировать описание для темы {topic_name}"