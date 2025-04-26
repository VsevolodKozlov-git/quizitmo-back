# app/models/course.py

from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class Course(Base):
    __tablename__ = "course"

    id_course: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="PK"
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Course title"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Course description"
    )
    id_user: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id_user"),
        nullable=False,
        index=True,
        comment="FK → User (owner)"
    )
