# app/endpoints/sse_quiz_results.py

import json
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.core.auth import get_current_user

from app.models.handle_quiz_attempt import HandleQuizAttempt
from app.models.quiz_attempt import QuizAttempt

router = APIRouter(prefix="/sse")


@router.get("/quiz_results")
async def sse_quiz_results(
    request: Request,
    current_user = Depends(get_current_user),
):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            async with async_session() as session:

                # 1) find all distinct quiz IDs with un‐handled attempts for this user
                quiz_q = (
                    select(QuizAttempt.id_quiz)
                    .join(
                        HandleQuizAttempt,
                        HandleQuizAttempt.id_quiz_attempt == QuizAttempt.id_quiz_attempt,
                    )
                    .where(
                        QuizAttempt.id_user == current_user.id_user,
                        HandleQuizAttempt.handled == False,
                    )
                    .distinct()
                )
                quiz_ids = (await session.execute(quiz_q)).scalars().all()

                for quiz_id in quiz_ids:
                    payload = {
                        "quiz_id": quiz_id,
                        "time": datetime.utcnow().isoformat() + "Z"
                    }
                    yield f"event: quiz_result\ndata: {json.dumps(payload)}\n\n"

                    # 2) mark **all** handle rows for this quiz as handled
                    await session.execute(
                        update(HandleQuizAttempt)
                        .where(
                            HandleQuizAttempt.id_quiz_attempt.in_(
                                select(QuizAttempt.id_quiz_attempt).where(
                                    QuizAttempt.id_quiz == quiz_id
                                )
                            ),
                            HandleQuizAttempt.handled == False
                        )
                        .values(handled=True)
                    )
                    await session.commit()

                await session.close()
                await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
