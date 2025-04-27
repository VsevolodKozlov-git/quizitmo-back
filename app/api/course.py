# app/endpoints/course.py

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.core.auth import get_current_user
from app.models.course import Course
from app.models.quiz import Quiz
from app.models.course_member import CourseMember
from app.models.user import User
from app.models.quiz_attempt import QuizAttempt

from app.schemas.course import (
    CourseCreate,
    CourseOut,
    CourseList,
    CourseDetailOut,
    QuizOut,
    UserOut,
    UserList,
    RemoveUserRequest,
    InviteUserRequest,
    QuizForYouOut,
    CourseForYouDetail,
)

router = APIRouter(prefix="/course")


@router.get("/your", response_model=CourseList)
async def list_your_courses(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Course).where(Course.id_user == current_user.id_user)
    )
    courses = list(result.scalars().all())
    return CourseList(courses=courses)


@router.post("/your/create", response_model=CourseOut, status_code=201)
async def create_course(
    payload: CourseCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    course = Course(
        title=payload.title,
        description=payload.description,
        id_user=current_user.id_user,
    )
    session.add(course)
    await session.commit()
    await session.refresh(course)
    return course


@router.get("/{id_course}/your", response_model=CourseDetailOut)
async def get_course_with_quizzes(
    id_course: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    course_row = await session.execute(
        select(Course).where(
            Course.id_course == id_course,
            Course.id_user == current_user.id_user,
        )
    )
    course = course_row.scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=403, detail="Forbidden")

    quiz_rows = await session.execute(
        select(Quiz).where(Quiz.id_course == id_course)
    )
    quizzes = quiz_rows.scalars().all()
    # build list of QuizOut via response_model
    return CourseDetailOut(title=course.title, quizes=quizzes)


@router.get("/{id_course}/member", response_model=UserList)
async def list_course_members(
    id_course: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # only course owner can list members
    owner_check = await session.execute(
        select(Course.id_course).where(
            Course.id_course == id_course,
            Course.id_user == current_user.id_user,
        )
    )
    if owner_check.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Forbidden")

    members = await session.execute(
        select(User).join(
            CourseMember,
            CourseMember.id_user == User.id_user
        ).where(CourseMember.id_course == id_course)
    )
    users = members.scalars().all()
    return UserList(users=users)


@router.post("/{id_course}/member/delete", status_code=204)
async def delete_course_member(
    id_course: int,
    payload: RemoveUserRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # only course owner can delete members
    owner_check = await session.execute(
        select(Course.id_course).where(
            Course.id_course == id_course,
            Course.id_user == current_user.id_user,
        )
    )
    if owner_check.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Forbidden")

    await session.execute(
        delete(CourseMember).where(
            CourseMember.id_course == id_course,
            CourseMember.id_user == payload.id_user,
        )
    )
    await session.commit()
    return Response(status_code=204)


@router.post("/{id_course}/member/invite", status_code=204)
async def invite_course_member(
    id_course: int,
    payload: InviteUserRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # only course owner may invite members
    owner = await session.execute(
        select(Course.id_course)
        .where(Course.id_course == id_course, Course.id_user == current_user.id_user)
    )
    if owner.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Forbidden")

    # find the user by email
    result = await session.execute(
        select(User).where(User.email == payload.email)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # ensure not already a member
    already = await session.execute(
        select(CourseMember.id_course_member)
        .where(
            CourseMember.id_course == id_course,
            CourseMember.id_user == user.id_user
        )
    )
    if already.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="User already a member")

    # create membership
    membership = CourseMember(id_course=id_course, id_user=user.id_user)
    session.add(membership)
    await session.commit()

    return Response(status_code=204)

@router.get("/for_you", response_model=CourseList)
async def list_for_you_courses(
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user),
):
    """
    Return all courses where the current user is a member.
    """
    result = await session.execute(
        select(Course)
        .join(CourseMember, CourseMember.id_course == Course.id_course)
        .where(CourseMember.id_user == current_user.id_user)
    )
    courses = result.scalars().all()
    return CourseList(courses=courses)


@router.get("/{id_course}/for_you", response_model=CourseForYouDetail)
async def get_course_for_you(
    id_course: int,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user),
):
    """
    Return course title and quizzes with progress info for the current user.
    """
        # fetch course title
    course_obj = await session.get(Course, id_course)
    if course_obj is None:
        raise HTTPException(status_code=404, detail="Course not found")

    # membership check
    membership = await session.execute(
        select(CourseMember.id_course_member)
        .where(
            CourseMember.id_course == id_course,
            CourseMember.id_user == current_user.id_user
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Forbidden")


    # fetch quizzes
    quiz_res = await session.execute(
        select(Quiz).where(Quiz.id_course == id_course)
    )
    quizzes = quiz_res.scalars().all()

    # for each quiz, compute is_complete and correct_ratio
    quiz_outputs: list[QuizForYouOut] = []
    for quiz in quizzes:
        # get latest attempt by date
        attempt_res = await session.execute(
            select(QuizAttempt)
            .where(
                QuizAttempt.id_quiz == quiz.id_quiz,
                QuizAttempt.id_user == current_user.id_user
            )
            .order_by(QuizAttempt.attempt_date.desc())
            .limit(1)
        )
        attempt = attempt_res.scalar_one_or_none()

        if attempt:
            total = attempt.total_answers or 0
            correct = attempt.correct_answers or 0
            ratio = correct / total if total > 0 else 0.0
            is_complete = ratio >= quiz.min_correct_ratio
            correct_ratio = ratio
        else:
            is_complete = False
            correct_ratio = None

        quiz_outputs.append(
            QuizForYouOut(
                id_quiz=quiz.id_quiz,
                title=quiz.title,
                description=quiz.description,
                min_correct_ratio=quiz.min_correct_ratio,
                coins=quiz.coins,
                is_complete=is_complete,
                correct_ratio=correct_ratio,
            )
        )

    return CourseForYouDetail(title=course_obj.title, quizes=quiz_outputs)