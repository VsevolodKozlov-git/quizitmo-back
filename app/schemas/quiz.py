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

class AnswerOptionDo(BaseModel):
    id_answer_option: int = Field(alias="id_answer")
    text: str

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class QuestionDo(BaseModel):
    id_question: int
    title: str
    text: str
    answers: List[AnswerOptionDo]

    model_config = {
        "from_attributes": True
    }


class QuizDoOut(BaseModel):
    title: str
    questions: List[QuestionDo]

    model_config = {
        "from_attributes": True
    }


class AnswerSubmit(BaseModel):
    id_question: int
    id_answer: int

    model_config = {
        "extra": "forbid"
    }


class QuizSubmitRequest(BaseModel):
    answers: List[AnswerSubmit]

    model_config = {
        "extra": "forbid"
    }


class QuizSubmitResponse(BaseModel):
    feedback: str
