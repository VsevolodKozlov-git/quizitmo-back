# app/models/user.py

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class User(Base):
    __tablename__ = "user"

    id_user: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="PK"
    )
    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="First name"
    )
    second_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="Second name"
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Email address"
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Username"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hashed password"
    )
