# app/models/answer_option.py

from sqlalchemy import Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class AnswerOption(Base):
    __tablename__ = "answer_option"

    id_answer_option: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="PK"
    )
    id_question: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("question.id_question"),
        nullable=False,
        index=True,
        comment="FK → Question"
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Option text"
    )
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="Correct option flag"
    )
