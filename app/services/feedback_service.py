# app/services/feedback_service.py

from typing import List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz
from app.models.course import Course
from app.models.question import Question
from app.models.answer_option import AnswerOption
from app.models.quiz_attempt_answer import QuizAttemptAnswer


async def generate_feedback_prompt(
    quiz_id: int,
    answers: List[Dict[str, int]],
    session: AsyncSession,
) -> str:
    """
    Build a feedback prompt for an LLM based on a quiz attempt.

    - quiz_id: id of the quiz taken
    - answers: list of {"id_question": ..., "id_answer": ...}

    Returns a single string prompt containing:
      * Course title & description
      * Quiz title & description
      * For each incorrectly answered question:
        - question title & text
        - study materials
        - text of the chosen (wrong) answer
        - text of the correct answer
      and a request for feedback.
    """

    # 1. Load quiz and course
    quiz = await session.get(Quiz, quiz_id)
    if not quiz:
        raise ValueError(f"Quiz {quiz_id} not found")

    course = await session.get(Course, quiz.id_course)
    if not course:
        raise ValueError(f"Course {quiz.id_course} not found")

    # 2. Header: course + quiz info
    prompt_lines = [
        f"Course: {course.title}",
        f"{course.description or ''}",
        "",
        f"Quiz: {quiz.title}",
        f"{quiz.description or ''}",
        "",
        "I answered the following questions incorrectly:"
    ]

    # 3. For each answer, check correctness and gather details if incorrect
    for ans in answers:
        q_id = ans["id_question"]
        a_id = ans["id_answer"]

        # load question
        question = await session.get(Question, q_id)
        if not question:
            continue

        # load the provided answer option
        provided = await session.get(AnswerOption, a_id)
        if not provided:
            continue

        # skip correct answers
        if provided.is_correct:
            continue

        # load the correct answer
        result = await session.execute(
            select(AnswerOption)
            .where(
                AnswerOption.id_question == q_id,
                AnswerOption.is_correct == True
            )
            .limit(1)
        )
        correct_option = result.scalar_one_or_none()
        correct_text = correct_option.text if correct_option else "<no correct answer found>"

        # append details
        prompt_lines.extend([
            "",
            f"Question: {question.title}",
            question.text,
            f"Study materials: {question.study_materials or 'None'}",
            f"My answer: {provided.text}",
            f"Correct answer: {correct_text}"
        ])

    # 4. Closing instruction
    prompt_lines.extend([
        "",
        "Please provide detailed feedback on these mistakes and how to improve."
    ])

    return "\n".join(prompt_lines)
