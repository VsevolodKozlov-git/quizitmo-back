# app/schemas/course.py

from typing import List, Optional

from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    title: str
    description: Optional[str]

    model_config = {
        "extra": "forbid"
    }


class CourseOut(BaseModel):
    id_course: int = Field(alias="id")
    title: str
    description: Optional[str]

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class QuizOut(BaseModel):
    id_quiz: int = Field(alias="id")
    title: str
    description: Optional[str]

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class CourseList(BaseModel):
    courses: List[CourseOut]

    model_config = {
        "from_attributes": True
    }


class CourseDetailOut(BaseModel):
    title: str
    quizes: List[QuizOut]

    model_config = {
        "from_attributes": True
    }


class UserOut(BaseModel):
    id_user: int = Field(alias="id_user")
    first_name: Optional[str]
    second_name: Optional[str] = Field(alias="last_name")
    email: str

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class UserList(BaseModel):
    users: List[UserOut]

    model_config = {
        "from_attributes": True
    }


class RemoveUserRequest(BaseModel):
    id_user: int

    model_config = {
        "extra": "forbid"
    }



class InviteUserRequest(BaseModel):
    email: str

    model_config = {
        "extra": "forbid"
    }
