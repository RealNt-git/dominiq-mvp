# backend/app/api/test_runner.py
import uuid
import subprocess
import json
import time
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TestRun  # ← ИСПРАВЛЕННЫЙ ИМПОРТ
from app.core.test_metrics import TEST_RUNS_TOTAL, TEST_DURATION
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test", tags=["Testing"])

def run_pytest_in_background(run_id: str, db_session: Session):
    """Фоновая задача для запуска тестов"""
    start_time = time.time()
    try:
        # Запускаем pytest и сохраняем JSON-отчёт
        result = subprocess.run(
            ["pytest", "tests/", "--json-report", "--json-report-file", f"/tmp/test_report_{run_id}.json"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        # Читаем JSON-отчёт
        with open(f"/tmp/test_report_{run_id}.json", "r") as f:
            report = json.load(f)
        
        duration = time.time() - start_time
        TEST_DURATION.observe(duration)
        status = "success" if report["summary"]["failed"] == 0 else "failed"
        TEST_RUNS_TOTAL.labels(status=status).inc()
        
        # Обновляем запись в БД
        run = db_session.query(TestRun).filter(TestRun.run_id == run_id).first()
        if run:
            run.status = status
            run.passed = report["summary"]["passed"]
            run.failed = report["summary"]["failed"]
            run.skipped = report["summary"].get("skipped", 0)
            run.total_tests = report["summary"]["total"]
            run.duration = duration
            run.completed_at = datetime.utcnow()
            run.details = report
            db_session.commit()
            
    except Exception as e:
        logger.error(f"Test run failed: {e}")
        TEST_RUNS_TOTAL.labels(status="error").inc()
        run = db_session.query(TestRun).filter(TestRun.run_id == run_id).first()
        if run:
            run.status = "error"
            run.completed_at = datetime.utcnow()
            db_session.commit()

@router.post("/run", status_code=202)
async def run_tests(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Запускает все тесты в фоновом режиме"""
    run_id = str(uuid.uuid4())
    
    test_run = TestRun(
        run_id=run_id,
        status="running"
    )
    db.add(test_run)
    db.commit()
    
    background_tasks.add_task(run_pytest_in_background, run_id, db)
    
    return {
        "run_id": run_id,
        "status": "running",
        "message": "Tests started in background"
    }

@router.get("/runs")
def get_test_runs(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Возвращает последние запуски тестов"""
    runs = db.query(TestRun).order_by(TestRun.created_at.desc()).limit(limit).all()
    return runs

@router.get("/runs/{run_id}")
def get_test_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Возвращает детали конкретного запуска"""
    run = db.query(TestRun).filter(TestRun.run_id == run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")
    return run