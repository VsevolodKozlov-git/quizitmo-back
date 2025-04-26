# app/models/quiz_attempt.py

from sqlalchemy import Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class QuizAttempt(Base):
    __tablename__ = "quiz_attempt"

    id_quiz_attempt: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="PK"
    )
    id_quiz: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quiz.id_quiz"),
        nullable=False,
        index=True,
        comment="FK → Quiz"
    )
    id_user: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id_user"),
        nullable=False,
        index=True,
        comment="FK → User"
    )
    attempt_date: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Attempt timestamp"
    )
    correct_answers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Count of correct answers"
    )
    total_answers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Count of total answers"
    )
    feedback: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="User feedback"
    )
