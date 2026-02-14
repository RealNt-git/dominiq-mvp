# backend/app/services/llm_client.py
# Клиент для взаимодействия с локальной Ollama (free model)
# Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Настройка логирования
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "phi3:mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
REQUEST_TIMEOUT = 120.0  # секунд


class LLMClient:
    """
    Асинхронный клиент для взаимодействия с локальными моделями через Ollama API.
    Поддерживает базовую генерацию и специализированное извлечение терминов.
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = LLM_MODEL,
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)

    async def close(self):
        """Закрытие HTTP-клиента."""
        await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying LLM request (attempt {retry_state.attempt_number})"
        ),
    )
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Отправляет промпт в модель и возвращает сгенерированный текст.

        :param prompt: текст запроса
        :param max_tokens: максимальное количество токенов в ответе (переопределяет дефолтное)
        :param temperature: температура сэмплирования
        :return: ответ модели (строка)
        :raises: httpx.HTTPError при ошибках запроса
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
            },
        }
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during LLM generate: {e}")
            raise

    async def extract_terms_with_context(
        self, text_chunk: str, domain: str
    ) -> List[Dict[str, Any]]:
        """
        Извлекает термины из текстового фрагмента с помощью модели.
        Ожидает ответ в формате JSON-массива объектов с полями:
        - term (str)
        - definition (str)
        - example (str, опционально)

        :param text_chunk: фрагмент текста для анализа
        :param domain: предметная область (например, "Ритейл")
        :return: список словарей с терминами или пустой список при ошибке
        """
        prompt = f"""
Ты — эксперт в области {domain}. Из следующего текста выдели все ключевые термины и для каждого найди определение и пример использования (если есть).
Ответ верни строго в формате JSON-массива объектов с полями: term, definition, example (может быть пустой строкой).
Текст: "{text_chunk}"
"""
        try:
            response_text = await self.generate(prompt, max_tokens=1000, temperature=0.1)
            # Пытаемся извлечь JSON из ответа (иногда модель может добавить пояснения)
            # Ищем первую '[' и последнюю ']'
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                terms = json.loads(json_str)
                if isinstance(terms, list):
                    # Фильтруем, чтобы каждый элемент содержал необходимые поля
                    validated = []
                    for item in terms:
                        if isinstance(item, dict) and "term" in item:
                            validated.append({
                                "term": item.get("term", ""),
                                "definition": item.get("definition", ""),
                                "example": item.get("example", ""),
                            })
                    return validated
            logger.warning(f"Could not parse JSON from LLM response: {response_text[:200]}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}. Response: {response_text[:200]}")
            return []
        except Exception as e:
            logger.error(f"Error in extract_terms_with_context: {e}")
            return []


# Для удобства можно создать экземпляр клиента как зависимость FastAPI
# Но в данном файле просто предоставляем класс.