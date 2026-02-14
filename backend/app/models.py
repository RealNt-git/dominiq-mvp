# backend/app/models.py
# Модели SQLAlchemy для MVP приложения Dominiq
# Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Float, JSON,
    Boolean, DateTime, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    total_xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Связи
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")


class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)

    topics = relationship("Topic", back_populates="domain", cascade="all, delete-orphan")
    terms = relationship("Term", back_populates="domain")


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        Index("ix_topic_domain_parent", "domain_id", "parent_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    unlock_condition = Column(JSON, nullable=True)  # Условие открытия (JSON)

    # Связи
    parent = relationship("Topic", remote_side=[id], backref="children")
    domain = relationship("Domain", back_populates="topics")
    terms = relationship("Term", back_populates="topic")
    quizzes = relationship("Quiz", back_populates="topic", cascade="all, delete-orphan")


class Term(Base):
    __tablename__ = "terms"
    __table_args__ = (
        Index("ix_term_domain_topic", "domain_id", "topic_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    term = Column(String, nullable=False, index=True)
    definition = Column(Text, nullable=False)
    example = Column(Text, nullable=True)
    mnemonic = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    source_document = Column(String, nullable=True)      # имя исходного файла
    source_fragment = Column(Text, nullable=True)        # выдержка для проверки
    created_at = Column(DateTime, server_default=func.now())

    # Связи
    domain = relationship("Domain", back_populates="terms")
    topic = relationship("Topic", back_populates="terms")
    flashcards = relationship("Flashcard", back_populates="term", cascade="all, delete-orphan")
    progress = relationship("UserProgress", back_populates="term", cascade="all, delete-orphan")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    term_id = Column(Integer, ForeignKey("terms.id"), nullable=False, unique=True)
    simplified_definition = Column(Text, nullable=True)
    hint = Column(Text, nullable=True)

    term = relationship("Term", back_populates="flashcards")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)

    topic = relationship("Topic", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    text = Column(Text, nullable=False)
    type = Column(String, nullable=False)       # "single", "multiple", "matching", "open"
    options = Column(JSON, nullable=True)       # варианты ответов (список строк)
    correct_answer = Column(JSON, nullable=False)  # правильный ответ
    explanation = Column(Text, nullable=True)

    quiz = relationship("Quiz", back_populates="questions")


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (
        Index("ix_user_progress_user_term", "user_id", "term_id", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    term_id = Column(Integer, ForeignKey("terms.id"), nullable=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=True)
    last_review = Column(DateTime, nullable=True)
    ease_factor = Column(Float, default=2.5)       # для SuperMemo
    interval = Column(Integer, default=0)           # интервал в днях
    repetitions = Column(Integer, default=0)        # количество повторений
    correct_streak = Column(Integer, default=0)     # дополнительно
    total_attempts = Column(Integer, default=0)

    user = relationship("User", back_populates="progress")
    term = relationship("Term", back_populates="progress")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(String, nullable=True)
    condition = Column(JSON, nullable=False)   # условие получения (JSON)

    users = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (
        Index("ix_user_achievement_user_ach", "user_id", "achievement_id", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="users")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    domain = Column(String, nullable=False)           # домен, для которого загружен документ
    content = Column(Text, nullable=False)            # полный текст
    uploaded_at = Column(DateTime, server_default=func.now())
    processed = Column(Boolean, default=False)        # флаг завершения обработки

    drafts_terms = relationship("DraftTerm", back_populates="document", cascade="all, delete-orphan")
    drafts_quizzes = relationship("DraftQuiz", back_populates="document", cascade="all, delete-orphan")


class DraftTerm(Base):
    __tablename__ = "draft_terms"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    term = Column(String, nullable=False)
    definition = Column(Text, nullable=True)
    example = Column(Text, nullable=True)
    context = Column(Text, nullable=True)             # контекст из документа
    mnemonic = Column(Text, nullable=True)
    status = Column(String, default="new")            # new, edited, approved, rejected
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    document = relationship("Document", back_populates="drafts_terms")


class DraftQuiz(Base):
    __tablename__ = "draft_quizzes"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    term_id = Column(Integer, nullable=False)          # связь с термином (не FK для черновика)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)              # варианты ответов
    correct = Column(Integer, nullable=False)          # индекс правильного варианта
    explanation = Column(Text, nullable=True)
    status = Column(String, default="new")             # new, edited, approved, rejected
    created_at = Column(DateTime, server_default=func.now())

    document = relationship("Document", back_populates="drafts_quizzes")