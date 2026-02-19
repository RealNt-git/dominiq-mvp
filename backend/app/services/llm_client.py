# backend/app/services/llm_client.py
# Клиент Ollama с подробным структурированным логированием и метриками Prometheus

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Импорт метрик Prometheus
from app.core.metrics import llm_requests_total, llm_request_duration_seconds

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "phi3:mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1500"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
REQUEST_TIMEOUT = 300.0

class LLMClient:
    def __init__(self, base_url=OLLAMA_BASE_URL, model=LLM_MODEL, max_tokens=MAX_TOKENS, temperature=TEMPERATURE):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
        logger.info("LLMClient initialized", extra={
            "action": "llm_init",
            "model": model,
            "base_url": base_url
        })

    async def close(self):
        await self._client.aclose()
        logger.info("LLMClient closed", extra={"action": "llm_close"})

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=lambda retry_state: logger.warning("Retrying LLM request", extra={
            "action": "llm_generate",
            "attempt": retry_state.attempt_number,
            "wait": retry_state.next_action.sleep
        })
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
        logger.info("Sending request to Ollama", extra={
            "action": "llm_generate",
            "model": self.model,
            "prompt_length": len(prompt),
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "event": "start"
        })
        start = time.time()
        status = "success"
        try:
            response = await self._client.post(url, json=payload)
            duration = time.time() - start
            logger.info("Ollama responded", extra={
                "action": "llm_generate",
                "status_code": response.status_code,
                "duration_sec": round(duration, 3),
                "event": "success"
            })
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            status = "error"
            duration = time.time() - start
            logger.error("Ollama request failed", extra={
                "action": "llm_generate",
                "duration_sec": round(duration, 3),
                "error": str(e),
                "exc_info": True
            })
            raise
        finally:
            # Обновляем метрики Prometheus
            llm_request_duration_seconds.labels(model=self.model).observe(duration)
            llm_requests_total.labels(model=self.model, status=status).inc()

    async def extract_terms_with_context(self, text_chunk: str, domain: str) -> List[Dict[str, Any]]:
        logger.info("Extracting terms with context", extra={
            "action": "extract_terms_with_context",
            "domain": domain,
            "chunk_length": len(text_chunk),
            "event": "start"
        })
        prompt = f"""
Ты — эксперт в области {domain}. Из следующего текста выдели все ключевые термины и для каждого найди определение и пример использования (если есть).
Ответ верни строго в формате JSON-массива объектов с полями: term, definition, example (может быть пустой строкой).
Текст: "{text_chunk}"
"""
        response_text = await self.generate(prompt, max_tokens=1000, temperature=0.1)
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
                    logger.info("Terms extracted successfully", extra={
                        "action": "extract_terms_with_context",
                        "domain": domain,
                        "terms_count": len(validated)
                    })
                    return validated
            logger.warning("Could not parse JSON from LLM response", extra={
                "action": "extract_terms_with_context",
                "domain": domain,
                "response_preview": response_text[:200]
            })
            return []
        except json.JSONDecodeError as e:
            logger.error("JSON decode error in extract_terms_with_context", extra={
                "action": "extract_terms_with_context",
                "domain": domain,
                "error": str(e)
            })
            return []
        except Exception as e:
            logger.error("Unexpected error in extract_terms_with_context", extra={
                "action": "extract_terms_with_context",
                "domain": domain,
                "error": str(e),
                "exc_info": True
            })
            return []