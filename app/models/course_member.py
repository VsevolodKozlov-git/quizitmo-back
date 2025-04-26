# app/models/course_member.py

from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class CourseMember(Base):
    __tablename__ = "course_member"

    id_course_member: Mapped[int] = mapped_column(
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
    id_user: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id_user"),
        nullable=False,
        index=True,
        comment="FK → User"
    )
