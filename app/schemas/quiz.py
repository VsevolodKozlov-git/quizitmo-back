# app/schemas/quiz.py

from typing import List, Optional
from pydantic import BaseModel, Field


class AnswerOptionCreate(BaseModel):
    text: str
    is_correct: bool

    model_config = {
        "extra": "forbid"
    }


class QuestionCreate(BaseModel):
    question_title: str = Field(alias="question_title")
    question_text: str = Field(alias="question_text")
    study_materials: Optional[str] = None
    answers: List[AnswerOptionCreate]

    model_config = {
        "extra": "forbid",
        "populate_by_name": True
    }


class QuizCreate(BaseModel):
    id_course: int
    title: str
    description: Optional[str] = None
    coins: int
    min_correct_ratio: float
    questions: List[QuestionCreate]

    model_config = {
        "extra": "forbid"
    }
