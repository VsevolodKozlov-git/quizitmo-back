# app/models/quiz_attempt_answer.py

from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class QuizAttemptAnswer(Base):
    __tablename__ = "quiz_attempt_answer"

    id_quiz_attempt_answer: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="PK"
    )
    id_quiz_attempt: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quiz_attempt.id_quiz_attempt", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → QuizAttempt"
    )
    id_question: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("question.id_question", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → Question"
    )
    id_answer_option: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("answer_option.id_answer_option", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → AnswerOption"
    )
