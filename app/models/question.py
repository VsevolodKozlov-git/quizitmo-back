# app/models/question.py

from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class Question(Base):
    __tablename__ = "question"

    id_question: Mapped[int] = mapped_column(
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
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Question title"
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Question text"
    )
    study_materials: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Supplemental materials"
    )
