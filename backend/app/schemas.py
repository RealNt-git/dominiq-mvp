# backend/app/schemas.py
# Pydantic схемы для MVP приложения Dominiq
# Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0
# Исправлено: regex -> pattern в QuestionBase

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator


# ---------- Базовые схемы ----------

class BaseSchema(BaseModel):
    class Config:
        orm_mode = True
        from_attributes = True  # для Pydantic v2


# ---------- User ----------

class UserLogin(BaseModel):
    email: str = Field(..., example="user@example.com")

    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Некорректный email')
        return v


class UserOut(BaseSchema):
    id: int
    email: str
    total_xp: int
    level: int
    created_at: datetime


# ---------- Domain ----------

class DomainBase(BaseSchema):
    name: str
    description: Optional[str] = None


class DomainCreate(DomainBase):
    pass


class DomainUpdate(DomainBase):
    name: Optional[str] = None


class DomainOut(DomainBase):
    id: int


# ---------- Topic ----------

class TopicBase(BaseSchema):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    domain_id: int
    unlock_condition: Optional[Dict[str, Any]] = None


class TopicCreate(TopicBase):
    pass


class TopicUpdate(TopicBase):
    name: Optional[str] = None
    domain_id: Optional[int] = None


class TopicOut(TopicBase):
    id: int


# ---------- Term ----------

class TermBase(BaseSchema):
    term: str
    definition: str
    example: Optional[str] = None
    mnemonic: Optional[str] = None
    image_url: Optional[str] = None
    domain_id: int
    topic_id: Optional[int] = None
    source_document: Optional[str] = None
    source_fragment: Optional[str] = None


class TermCreate(TermBase):
    pass


class TermUpdate(TermBase):
    term: Optional[str] = None
    definition: Optional[str] = None
    domain_id: Optional[int] = None


class TermOut(TermBase):
    id: int
    created_at: datetime


# ---------- Flashcard ----------

class FlashcardBase(BaseSchema):
    term_id: int
    simplified_definition: Optional[str] = None
    hint: Optional[str] = None


class FlashcardCreate(FlashcardBase):
    pass


class FlashcardUpdate(FlashcardBase):
    term_id: Optional[int] = None


class FlashcardOut(FlashcardBase):
    id: int


# ---------- Quiz ----------

class QuizBase(BaseSchema):
    title: str
    topic_id: Optional[int] = None  # <-- изменено: поле стало необязательным


class QuizCreate(QuizBase):
    pass


class QuizUpdate(QuizBase):
    title: Optional[str] = None
    topic_id: Optional[int] = None


class QuizOut(QuizBase):
    id: int


# ---------- Question ----------

class QuestionBase(BaseSchema):
    quiz_id: int
    text: str
    type: str = Field(..., pattern="^(single|multiple|matching|open)$")  # Исправлено: regex -> pattern
    options: Optional[List[str]] = None
    correct_answer: Union[int, List[int], str, Dict]  # зависит от типа
    explanation: Optional[str] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(QuestionBase):
    quiz_id: Optional[int] = None
    text: Optional[str] = None
    type: Optional[str] = None


class QuestionOut(QuestionBase):
    id: int


# ---------- UserProgress ----------

class UserProgressBase(BaseSchema):
    user_id: int
    term_id: Optional[int] = None
    quiz_id: Optional[int] = None
    last_review: Optional[datetime] = None
    ease_factor: float = 2.5
    interval: int = 0
    repetitions: int = 0
    correct_streak: int = 0
    total_attempts: int = 0


class UserProgressCreate(UserProgressBase):
    pass


class UserProgressUpdate(BaseSchema):
    last_review: Optional[datetime] = None
    ease_factor: Optional[float] = None
    interval: Optional[int] = None
    repetitions: Optional[int] = None
    correct_streak: Optional[int] = None
    total_attempts: Optional[int] = None


class UserProgressOut(UserProgressBase):
    id: int


# ---------- Achievement ----------

class AchievementBase(BaseSchema):
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    condition: Dict[str, Any]


class AchievementCreate(AchievementBase):
    pass


class AchievementUpdate(AchievementBase):
    name: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None


class AchievementOut(AchievementBase):
    id: int


# ---------- UserAchievement ----------

class UserAchievementBase(BaseSchema):
    user_id: int
    achievement_id: int


class UserAchievementCreate(UserAchievementBase):
    pass


class UserAchievementOut(UserAchievementBase):
    id: int
    earned_at: datetime


# ---------- Document ----------

class DocumentBase(BaseSchema):
    filename: str
    domain: str
    content: str
    processed: bool = False


class DocumentCreate(DocumentBase):
    pass


class DocumentOut(DocumentBase):
    id: int
    uploaded_at: datetime


# ---------- DraftTerm ----------

class DraftTermBase(BaseSchema):
    document_id: int
    term: str
    definition: Optional[str] = None
    example: Optional[str] = None
    context: Optional[str] = None
    status: str = "new"  # new, edited, approved, rejected


class DraftTermCreate(DraftTermBase):
    pass


class DraftTermUpdate(BaseSchema):
    term: Optional[str] = None
    definition: Optional[str] = None
    example: Optional[str] = None
    context: Optional[str] = None
    status: Optional[str] = None


class DraftTermOut(DraftTermBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    mnemonic: Optional[str] = None


# ---------- DraftQuiz ----------

class DraftQuizBase(BaseSchema):
    document_id: int
    term_id: int
    question: str
    options: Optional[List[str]] = None
    correct: int
    explanation: Optional[str] = None
    status: str = "new"


class DraftQuizCreate(DraftQuizBase):
    pass


class DraftQuizUpdate(BaseSchema):
    question: Optional[str] = None
    options: Optional[List[str]] = None
    correct: Optional[int] = None
    explanation: Optional[str] = None
    status: Optional[str] = None


class DraftQuizOut(DraftQuizBase):
    id: int
    created_at: datetime


# ---------- Схемы для ответов с вложенными данными ----------

class TopicWithChildren(TopicOut):
    children: List['TopicOut'] = []


class TermWithFlashcard(TermOut):
    flashcard: Optional[FlashcardOut] = None


class QuizWithQuestions(QuizOut):
    questions: List[QuestionOut] = []


# ---------- Схемы для запросов AI-ассистента ----------

class DocumentUploadResponse(BaseSchema):
    document_id: int
    message: str = "Документ загружен и обработан"


class DraftApproveRequest(BaseModel):
    document_id: int
    draft_ids: Optional[List[int]] = None  # если None, утвердить все


# ---------- Схемы для обучения ----------

class CardForReview(BaseSchema):
    id: int
    term: str
    definition: str
    example: Optional[str] = None
    simplified_definition: Optional[str] = None
    hint: Optional[str] = None


class CardReviewRequest(BaseModel):
    card_id: int
    known: bool


class QuizQuestionForUser(BaseSchema):
    id: int
    text: str
    type: str
    options: Optional[List[str]] = None  # правильный ответ не передаём


class QuizSubmitRequest(BaseModel):
    quiz_id: int
    answers: List[Union[int, List[int], str]]  # зависит от типа вопросов


class QuizResult(BaseSchema):
    quiz_id: int
    correct_count: int
    total_count: int
    xp_earned: int


# ---------- Схемы для геймификации ----------

class UserProgressSummary(BaseSchema):
    total_xp: int
    level: int
    cards_studied: int
    quizzes_passed: int
    achievements_count: int


class AchievementWithEarned(AchievementOut):
    earned: bool
    earned_at: Optional[datetime] = None