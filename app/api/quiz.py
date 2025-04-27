# app/endpoints/quiz.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.core.auth import get_current_user

from app.models.course import Course
from app.models.course_member import CourseMember
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.answer_option import AnswerOption

from app.schemas.quiz import QuizCreate
from app.schemas.course import QuizOut

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.post("/create", response_model=QuizOut, status_code=201)
async def create_quiz(
    payload: QuizCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # verify user is part of the course (owner or member)
    owner_q = select(Course.id_course).where(
        Course.id_course == payload.id_course,
        Course.id_user == current_user.id_user,
    )
    member_q = select(CourseMember.id_course_member).where(
        CourseMember.id_course == payload.id_course,
        CourseMember.id_user == current_user.id_user,
    )

    owner = await session.execute(owner_q)
    member = await session.execute(member_q)
    if owner.scalar_one_or_none() is None and member.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Forbidden")

    # create the quiz
    quiz = Quiz(
        id_course=payload.id_course,
        title=payload.title,
        description=payload.description,
        coins=payload.coins,
        min_correct_ratio=payload.min_correct_ratio,
    )
    session.add(quiz)
    await session.flush()  # populate quiz.id_quiz

    # create questions and their answer options
    for q in payload.questions:
        question = Question(
            id_quiz=quiz.id_quiz,
            title=q.question_title,
            text=q.question_text,
            study_materials=q.study_materials,
        )
        session.add(question)
        await session.flush()  # populate question.id_question

        for a in q.answers:
            ao = AnswerOption(
                id_question=question.id_question,
                text=a.text,
                is_correct=a.is_correct,
            )
            session.add(ao)

    # commit all and refresh quiz
    await session.commit()
    await session.refresh(quiz)

    return quiz
