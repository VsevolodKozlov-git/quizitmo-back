from fastapi import APIRouter, Depends
from app.schemas.llm import MutationPayload, LLMResponse
from app.services.llm_client import send_to_llm
from app.services.prompts import generate_quiz_help_prompt
from app.core.auth import get_current_user
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/llm')

@router.post("/get", response_model=LLMResponse)
async def get_llm_response(
    payload: MutationPayload,
    _: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    system_prompt = generate_quiz_help_prompt(payload)

    messages = [
        {"role": "system", "content": system_prompt},
        *[
            {"role": msg.from_, "content": msg.text}
            for msg in payload.prev_messages
        ],
        {"role": "user", "content": payload.user_message}
    ]

    response_text = await send_to_llm(messages)

    return {"text": response_text}