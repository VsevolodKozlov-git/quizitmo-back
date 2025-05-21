# app/models/file.py

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class File(Base):
    __tablename__ = "file"

    id_file: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="PK"
    )
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Stored filename"
    )
    id_course: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("course.id_course", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → Course"
    )
