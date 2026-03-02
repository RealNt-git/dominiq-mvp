from prometheus_client import Counter, Histogram, Gauge

# Счётчик загруженных документов
document_upload_total = Counter(
    'document_upload_total',
    'Total number of document uploads'
)

# Гистограмма времени обработки документа
document_processing_duration_seconds = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration in seconds',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# Количество активных пользователей (можно обновлять через API)
active_users = Gauge(
    'active_users',
    'Number of active users (with sessions in last 5 min)'
)

# Гистограмма длительности HTTP-запросов (может использоваться для кастомных роутов)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status_code']
)

llm_requests_total = Counter(
    'llm_requests_total',
    'Total number of LLM requests',
    ['model', 'status']  # status: success, error
)

llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['model'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120]
)

# Новые метрики для Langflow
langflow_requests_total = Counter(
    'langflow_requests_total',
    'Total number of Langflow requests',
    ['flow_id', 'status']  # status: success, error
)

langflow_request_duration_seconds = Histogram(
    'langflow_request_duration_seconds',
    'Langflow request duration in seconds',
    ['flow_id'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120]
)