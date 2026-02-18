# backend/app/models/test_models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from sqlalchemy.sql import func
from app.database import Base

class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, nullable=False)  # UUID запуска
    status = Column(String, nullable=False)  # success, failed, running, error
    total_tests = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    duration = Column(Float, nullable=True)
    report_path = Column(String, nullable=True)  # путь к HTML-отчёту
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    details = Column(JSON, nullable=True)  # детали по каждому тесту