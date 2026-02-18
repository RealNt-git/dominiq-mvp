###backend/app/core/test_metrics.py
from prometheus_client import Counter, Histogram

TEST_RUNS_TOTAL = Counter(
    'test_runs_total',
    'Total number of test runs',
    ['status']  # success, failed, error
)

TEST_DURATION = Histogram(
    'test_duration_seconds',
    'Test run duration in seconds',
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)