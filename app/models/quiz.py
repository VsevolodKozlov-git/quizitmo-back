# app/models/quiz.py

from sqlalchemy import Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class Quiz(Base):
    __tablename__ = "quiz"

    id_quiz: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="PK"
    )
    id_course: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("course.id_course"),
        nullable=False,
        index=True,
        comment="FK → Course"
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Quiz title"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Quiz description"
    )
    coins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Reward coins"
    )
    min_correct_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Minimum correct‐answer ratio"
    )
