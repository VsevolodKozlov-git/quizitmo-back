# app/endpoints/course.py

import asyncio
import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
)
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.testing.assertsql import CountStatements

from app.core.auth import get_current_user
from app.core.settings import Settings
from app.db.session import get_session
from app.models.answer_option import AnswerOption
from app.models.course import Course
from app.models.course_member import CourseMember
from app.models.file import File as CourseFile
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_attempt_answer import QuizAttemptAnswer
from app.models.user import User
from app.schemas.course import (
    CourseCreate,
    CourseDetailOut,
    CourseForYouDetail,
    CourseList,
    CourseOut,
    InviteUserRequest,
    QuizForYouOut,
    QuizOut,
    RemoveUserRequest,
    UserList,
    UserOut,
)
from app.schemas.file import FileOut, RemoveFileRequest
from app.services.llm_client import save_pdf_to_db


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
    current_user=Depends(get_current_user),
):
    # fetch course
    course_obj = await session.get(Course, id_course)
    if course_obj is None:
        raise HTTPException(status_code=404, detail="Course not found")

    # membership check
    membership = await session.execute(
        select(CourseMember.id_course_member).where(
            CourseMember.id_course == id_course,
            CourseMember.id_user == current_user.id_user,
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Forbidden")

    # fetch quizzes
    quiz_res = await session.execute(
        select(Quiz).where(Quiz.id_course == id_course)
    )
    quizzes = quiz_res.scalars().all()

    quiz_outputs: list[QuizForYouOut] = []
    for quiz in quizzes:
        # latest attempt
        attempt_res = await session.execute(
            select(QuizAttempt)
            .where(
                QuizAttempt.id_quiz == quiz.id_quiz,
                QuizAttempt.id_user == current_user.id_user,
            )
            .order_by(QuizAttempt.attempt_date.desc())
            .limit(1)
        )
        attempt = attempt_res.scalar_one_or_none()

        # "is_complete" is true if any attempt exists
        is_complete = attempt is not None

        # compute correct_ratio only if an attempt exists
        if attempt:
            # count total answers in this attempt
            total_res = await session.execute(
                select(func.count())
                .select_from(QuizAttemptAnswer)
                .where(QuizAttemptAnswer.id_quiz_attempt == attempt.id_quiz_attempt)
            )
            total = total_res.scalar_one() or 0

            # count correct answers via join to AnswerOption
            correct_res = await session.execute(
                select(func.count())
                .select_from(QuizAttemptAnswer)
                .join(
                    AnswerOption,
                    AnswerOption.id_answer_option == QuizAttemptAnswer.id_answer_option
                )
                .where(
                    QuizAttemptAnswer.id_quiz_attempt == attempt.id_quiz_attempt,
                    AnswerOption.is_correct == True
                )
            )
            correct = correct_res.scalar_one() or 0

            correct_ratio = (correct / total) if total > 0 else 0.0
        else:
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

@router.post(
    "/{course_id}/add_file",
    status_code=201,
    summary="Upload a PDF file and attach it to a course",
)
async def add_file_to_course(
    course_id: int,
    upload: UploadFile = File(..., description="A PDF document"),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # 1. Verify ownership
    course_obj = await session.get(Course, course_id)
    if course_obj is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course_obj.id_user != current_user.id_user:
        raise HTTPException(status_code=403, detail="Forbidden")

    # 2. Validate PDF
    if upload.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF uploads are allowed"
        )

    # 3. Save file to disk
    upload_dir = os.path.join("uploads", f"course_{course_id}")
    os.makedirs(upload_dir, exist_ok=True)

    # use uuid to avoid collisions
    filename = f"{upload.filename}"
    # path = os.path.join(upload_dir, filename)
    # contents = await upload.read()
    # with open(path, "wb") as f:
    #     f.write(contents)

    # 4. Record in DB
    file_rec = CourseFile(
        file_name=filename,
        id_course=course_id
    )
    session.add(file_rec)
    await session.commit()
    # save_pdf_to_db(pdf_path=file_path, file_name=safe_name, collection_name=collection_name)
    await asyncio.sleep(3)

    return {"msg": "ok"}


@router.get(
    "/{course_id}/file",
    response_model=list[FileOut],
    summary="List uploaded files for a course"
)
async def list_course_files(
    course_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # verify ownership
    course_obj = await session.get(Course, course_id)
    if course_obj is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course_obj.id_user != current_user.id_user:
        raise HTTPException(status_code=403, detail="Forbidden")

    res = await session.execute(
        select(CourseFile).where(CourseFile.id_course == course_id)
    )
    files = res.scalars().all()
    return files


@router.post(
    "/{course_id}/file/delete",
    status_code=200,
    summary="Delete a file from a course"
)
async def delete_course_file(
    course_id: int,
    payload: RemoveFileRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # verify ownership
    course_obj = await session.get(Course, course_id)
    if course_obj is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course_obj.id_user != current_user.id_user:
        raise HTTPException(status_code=403, detail="Forbidden")

    # verify file belongs to this course
    res = await session.execute(
        select(CourseFile).where(
            CourseFile.id_file == payload.id_file,
            CourseFile.id_course == course_id
        )
    )
    file_rec = res.scalar_one_or_none()
    if file_rec is None:
        raise HTTPException(status_code=404, detail="File not found in this course")

    # delete the DB record
    await session.execute(
        delete(CourseFile).where(CourseFile.id_file == payload.id_file)
    )
    await session.commit()

    return {"msg": "ok"}