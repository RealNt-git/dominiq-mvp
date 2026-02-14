# backend/app/services/llm_client.py
# Клиент Ollama с логированием времени

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "phi3:mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
REQUEST_TIMEOUT = 240.0

class LLMClient:
    def __init__(self, base_url=OLLAMA_BASE_URL, model=LLM_MODEL, max_tokens=MAX_TOKENS, temperature=TEMPERATURE):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
        logger.debug(f"LLMClient initialized: model={model}, base_url={base_url}")

    async def close(self):
        await self._client.aclose()
        logger.debug("LLMClient closed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=lambda retry_state: logger.warning(f"Retrying LLM request (attempt {retry_state.attempt_number})")
    )
    async def generate(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
            }
        }
        logger.info(f"Sending request to Ollama, prompt length: {len(prompt)} chars")
        start = time.time()
        try:
            response = await self._client.post(url, json=payload)
            duration = time.time() - start
            logger.info(f"Ollama responded in {duration:.2f}s, status {response.status_code}")
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            logger.error(f"Ollama request failed after {time.time()-start:.2f}s: {e}")
            raise

    async def extract_terms_with_context(self, text_chunk: str, domain: str) -> List[Dict[str, Any]]:
        logger.debug(f"extract_terms_with_context called for domain {domain}, chunk length {len(text_chunk)}")
        prompt = f"""
Ты — эксперт в области {domain}. Из следующего текста выдели все ключевые термины и для каждого найди определение и пример использования (если есть).
Ответ верни строго в формате JSON-массива объектов с полями: term, definition, example (может быть пустой строкой).
Текст: "{text_chunk}"
"""
        response_text = await self.generate(prompt, max_tokens=1000, temperature=0.1)
        # Парсинг JSON (как ранее)
        try:
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                terms = json.loads(json_str)
                if isinstance(terms, list):
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