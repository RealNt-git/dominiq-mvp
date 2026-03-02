# backend/app/services/langflow_client.py
import os
import time
import httpx
import logging
from typing import Dict, Any, Optional

from app.core.metrics import langflow_requests_total, langflow_request_duration_seconds

logger = logging.getLogger(__name__)

class LangflowClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("LANGFLOW_API_URL", "http://langflow:7860/api/v1")
        self.client = httpx.AsyncClient(timeout=300.0)  # большой таймаут для длительных генераций

    async def run_flow(self, flow_id: str, inputs: Dict[str, Any]) -> str:
        """
        Запускает flow в Langflow с переданными входными параметрами.
        Возвращает текстовый результат из первого выхода.
        """
        url = f"{self.base_url}/run/{flow_id}"
        payload = {
            "inputs": inputs,
            "output_type": "text",
            "input_type": "text"
        }
        start_time = time.time()
        status = "error"
        try:
            logger.info(f"Calling Langflow flow {flow_id} with inputs: {inputs}")
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            # Предполагаемая структура ответа: data['outputs'][0]['results']['text']
            logger.info(f"Langflow response data: {data}")
            result = self._extract_result(data)
            status = "success"
            logger.info(f"Langflow flow {flow_id} returned {len(result)} chars")
            return result
        except Exception as e:
            logger.error(f"Langflow flow {flow_id} failed: {e}", exc_info=True)
            raise
        finally:
            duration = time.time() - start_time
            langflow_request_duration_seconds.labels(flow_id=flow_id).observe(duration)
            langflow_requests_total.labels(flow_id=flow_id, status=status).inc()

    def _extract_result(self, data: Dict) -> str:
        """
        Извлекает текстовый результат из ответа Langflow.
        Приоритет: messages[0].message -> results.text.data.text -> полный дамп.
        В зависимости от версии Langflow структура может отличаться.
        Пример для последних версий:
        {
            "outputs": [
                {
                    "results": {
                        "text": "..."
                    }
                }
            ]
        }
        """
        try:
        # Основной путь: outputs[0].outputs[0].messages[0].message
            return data['outputs'][0]['outputs'][0]['messages'][0]['message']
        except (KeyError, IndexError):
            try:
                  # Альтернативный путь: outputs[0].outputs[0].results.text.data.text
                  return data['outputs'][0]['outputs'][0]['results']['text']['data']['text']
            except (KeyError, IndexError):
                logger.warning(f"Unexpected Langflow response structure: {data}")
                return str(data)
    
    async def close(self):
        await self.client.aclose()