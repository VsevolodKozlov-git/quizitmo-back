# app/endpoints/quiz.py

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.answer_option import AnswerOption
from app.models.course import Course
from app.models.course_member import CourseMember
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_attempt_answer import QuizAttemptAnswer
from app.schemas.course import QuizOut
from app.schemas.quiz import (
    AnswerOptionDo,
    AnswerOptionResult,
    QuestionDo,
    QuestionResult,
    QuizCreate,
    QuizDoOut,
    QuizResultsOut,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.services.feedback_service import generate_feedback_prompt
from app.services.llm_client import send_to_llm


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

@router.get("/for_you/{quiz_id}/do", response_model=QuizDoOut)
async def do_quiz(
    quiz_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # 1. Load quiz
    quiz_obj = await session.get(Quiz, quiz_id)
    if not quiz_obj:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # 2. Membership check
    member_res = await session.execute(
        select(CourseMember.id_course_member).where(
            CourseMember.id_course == quiz_obj.id_course,
            CourseMember.id_user == current_user.id_user,
        )
    )
    if member_res.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Forbidden")

    # 3. Ensure not yet taken
    taken_res = await session.execute(
        select(QuizAttempt.id_quiz_attempt).where(
            QuizAttempt.id_quiz == quiz_id,
            QuizAttempt.id_user == current_user.id_user,
        )
    )
    if taken_res.scalar_one_or_none() is not None:
        raise HTTPException(status_code=403, detail="Quiz already taken")

    # 4. Fetch questions
    q_res = await session.execute(
        select(Question).where(Question.id_quiz == quiz_id)
    )
    questions = q_res.scalars().all()

    # 5. Fetch all answer options in one go
    question_ids = [q.id_question for q in questions]
    ao_res = await session.execute(
        select(AnswerOption).where(AnswerOption.id_question.in_(question_ids))
    )
    all_options = ao_res.scalars().all()
    opts_map: dict[int, list[AnswerOption]] = {}
    for opt in all_options:
        opts_map.setdefault(opt.id_question, []).append(opt)

    # 6. Assemble response
    question_dos = []
    for q in questions:
        q_opts = opts_map.get(q.id_question, [])
        question_dos.append(
            QuestionDo(
                id_question=q.id_question,
                title=q.title,
                text=q.text,
                answers=q_opts,
            )
        )

    return QuizDoOut(title=quiz_obj.title, questions=question_dos)


@router.post("/for_you/{quiz_id}/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    quiz_id: int,
    payload: QuizSubmitRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # 1. Load quiz
    quiz_obj = await session.get(Quiz, quiz_id)
    if not quiz_obj:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # 2. Membership check
    member_res = await session.execute(
        select(CourseMember.id_course_member).where(
            CourseMember.id_course == quiz_obj.id_course,
            CourseMember.id_user == current_user.id_user,
        )
    )
    if member_res.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Forbidden")

    # 3. Ensure not yet taken
    taken_res = await session.execute(
        select(QuizAttempt.id_quiz_attempt).where(
            QuizAttempt.id_quiz == quiz_id,
            QuizAttempt.id_user == current_user.id_user,
        )
    )
    if taken_res.scalar_one_or_none() is not None:
        raise HTTPException(status_code=403, detail="Quiz already taken")

    # 4. Create QuizAttempt
    attempt = QuizAttempt(
        id_quiz=quiz_id,
        id_user=current_user.id_user,
        attempt_date=datetime.utcnow(),
    )
    session.add(attempt)
    await session.flush()  # populate attempt.id_quiz_attempt

    # 5. Persist each answer
    for ans in payload.answers:
        answer_record = QuizAttemptAnswer(
            id_quiz_attempt=attempt.id_quiz_attempt,
            id_question=ans.id_question,
            id_answer_option=ans.id_answer,
        )
        session.add(answer_record)

    await session.commit()

    # 6. Generate feedback
    answers_list = [
        {"id_question": ans.id_question, "id_answer": ans.id_answer}
        for ans in payload.answers
    ]
    prompt = await generate_feedback_prompt(quiz_id, answers_list, session)
    feedback = await send_to_llm(prompt)

    # 7. Persist feedback on attempt
    attempt.feedback = feedback
    session.add(attempt)
    await session.commit()

    return QuizSubmitResponse(feedback=feedback)



@router.get("/for_you/{quiz_id}/results", response_model=QuizResultsOut)
async def get_quiz_results(
    quiz_id: int,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user),
):
    # 1. Ensure the user has taken this quiz
    attempt_res = await session.execute(
        select(QuizAttempt)
        .where(
            QuizAttempt.id_quiz == quiz_id,
            QuizAttempt.id_user == current_user.id_user,
        )
        .order_by(QuizAttempt.attempt_date.desc())
        .limit(1)
    )
    attempt = attempt_res.scalar_one_or_none()
    if attempt is None:
        raise HTTPException(status_code=422, detail="No quiz result found")

    # 2. Load quiz
    quiz = await session.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # 3. Fetch all questions for this quiz
    q_res = await session.execute(
        select(Question).where(Question.id_quiz == quiz_id)
    )
    questions = q_res.scalars().all()

    # 4. Fetch all answer options for these questions
    question_ids = [q.id_question for q in questions]
    ao_res = await session.execute(
        select(AnswerOption).where(AnswerOption.id_question.in_(question_ids))
    )
    all_options = ao_res.scalars().all()
    options_map: dict[int, list[AnswerOption]] = {}
    for opt in all_options:
        options_map.setdefault(opt.id_question, []).append(opt)

    # 5. Fetch the user's selected answers in this attempt
    aa_res = await session.execute(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.id_quiz_attempt == attempt.id_quiz_attempt
        )
    )
    answered = aa_res.scalars().all()
    selected_map = {a.id_question: a.id_answer_option for a in answered}

    # 6. Build per-question result entries
    question_results: list[QuestionResult] = []
    correct_count = 0
    for q in questions:
        opts = options_map.get(q.id_question, [])
        # find correct option
        correct_opt = next((o for o in opts if o.is_correct), None)
        correct_id = correct_opt.id_answer_option if correct_opt else None

        # find selected
        selected_id = selected_map.get(q.id_question)

        # tally correctness
        if selected_id is not None and selected_id == correct_id:
            correct_count += 1

        ao_results = [
            AnswerOptionResult(id_answer=o.id_answer_option, text=o.text)
            for o in opts
        ]

        question_results.append(
            QuestionResult(
                id_question=q.id_question,
                title=q.title,
                text=q.text,
                answers=ao_results,
                id_answer_correct=correct_id,
                id_answer_selected=selected_id,
            )
        )

    total = len(question_results)
    is_min = (correct_count / total) >= quiz.min_correct_ratio if total > 0 else False

    return QuizResultsOut(
        title=quiz.title,
        questions=question_results,
        correct_answers=correct_count,
        total_answers=total,
        is_min_correct_ratio=is_min,
        coins=quiz.coins,
        feedback=attempt.feedback or "",
    )