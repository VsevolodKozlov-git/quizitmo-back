# app/models/handle_quiz_attempt.py

from sqlalchemy import Integer, ForeignKey, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class HandleQuizAttempt(Base):
    __tablename__ = "handle_quiz_attempt"

    id_handle_quiz_attempt: Mapped[int] = mapped_column(
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
    handled: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
        comment="Handled flag"
    )
