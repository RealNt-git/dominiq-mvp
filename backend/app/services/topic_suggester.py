# backend/app/services/topic_suggester.py
import json
import logging
import time  # добавлен импорт time
from typing import List, Dict, Any

from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

async def suggest_topics(domain: str, role: str = "аналитик") -> List[Dict[str, str]]:
    """
    Запрашивает у LLM список популярных тем для заданной роли и домена.
    Возвращает список словарей с полями 'name' и 'description'.
    """
    llm = LLMClient()
    prompt = f"""
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
    try:
        response = await llm.generate(prompt, max_tokens=1500, temperature=0.3)
        logger.info("LLM response for topic suggestions", extra={
            "action": "suggest_topics",
            "domain": domain,
            "role": role,
            "response_length": len(response)
        })
        # Парсим JSON
        start = response.find('[')
        end = response.rfind(']') + 1
        if start != -1 and end > start:
            json_str = response[start:end]
            topics = json.loads(json_str)
            if isinstance(topics, list):
                validated = []
                for t in topics:
                    if isinstance(t, dict) and "name" in t and "description" in t:
                        validated.append({"name": t["name"], "description": t["description"]})
                logger.info(f"Parsed {len(validated)} topic suggestions", extra={
                    "action": "suggest_topics",
                    "domain": domain,
                    "topics_count": len(validated)
                })
                return validated
            else:
                logger.warning("LLM response is not a list", extra={"action": "suggest_topics", "response": response[:200]})
                return []
        else:
            logger.warning("Could not find JSON array in LLM response", extra={"action": "suggest_topics", "response": response[:200]})
            return []
    except Exception as e:
        logger.error("Error suggesting topics", extra={"action": "suggest_topics", "domain": domain, "error": str(e)})
        return []
    finally:
        await llm.close()


async def generate_topic_content(domain: str, topic_name: str) -> str:
    """
    Генерирует статью по заданной теме в рамках домена.
    Возвращает текст объёмом около 500-1000 символов (сокращено для ускорения).
    """
    llm = LLMClient()
    prompt = f"""
Ты — эксперт в области {domain}. Напиши подробную статью для аналитика на тему "{topic_name}".
Статья должна объяснять, что это такое, в каких бизнес-процессах применяется, привести примеры.
Объём — примерно 500-1000 символов. Текст должен быть на русском языке.
Не используй markdown, только обычный текст.
"""
    start_time = time.time()
    try:
        response = await llm.generate(prompt, max_tokens=1500, temperature=0.3)
        duration = time.time() - start_time
        logger.info("Generated content for topic", extra={
            "action": "generate_topic_content",
            "domain": domain,
            "topic": topic_name,
            "duration_sec": round(duration, 2),
            "content_length": len(response)
        })
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Error generating topic content", exc_info=True, extra={
            "action": "generate_topic_content",
            "domain": domain,
            "topic": topic_name,
            "duration_sec": round(duration, 2)
        })
        return f"Ошибка генерации контента для темы {topic_name}"
    finally:
        await llm.close()


async def describe_topic(domain: str, topic_name: str) -> str:
    """
    Генерирует краткое описание для заданной темы в рамках домена.
    Возвращает описание (до 500 символов) без лишних фраз.
    """
    llm = LLMClient()
    prompt = f"""
Ты — эксперт в области {domain}. Напиши краткое описание (не более 500 символов) для темы "{topic_name}" для аналитика.
Опиши, что это такое, в каких бизнес-процессах применяется, приведи пример.
Твой ответ должен содержать только описание, без каких-либо дополнительных фраз, комментариев или повторения задания.
Начинай сразу с текста описания.
"""
    start_time = time.time()
    try:
        response = await llm.generate(prompt, max_tokens=300, temperature=0.3)
        response = response.strip()
        duration = time.time() - start_time
        # Дополнительная проверка: если ответ начинается с типичных фраз промпта, просто логируем предупреждение
        unwanted_starters = [
            "ты — эксперт",
            "напиши краткое описание",
            "опиши, что это такое",
            "для темы",
            "твой ответ должен содержать"
        ]
        lower_response = response.lower()
        for starter in unwanted_starters:
            if lower_response.startswith(starter):
                logger.warning("Response may contain prompt leftovers", extra={
                    "topic": topic_name,
                    "response_start": response[:100]
                })
                break
        logger.info("Generated description for topic", extra={
            "action": "describe_topic",
            "domain": domain,
            "topic": topic_name,
            "duration_sec": round(duration, 2),
            "description_length": len(response)
        })
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Error describing topic", exc_info=True, extra={
            "action": "describe_topic",
            "domain": domain,
            "topic": topic_name,
            "duration_sec": round(duration, 2)
        })
        return f"Не удалось сгенерировать описание для темы {topic_name}"
    finally:
        await llm.close()