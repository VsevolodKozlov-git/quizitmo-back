from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, List

class Message(BaseModel):
    text: str
    from_: Literal['user', 'bot'] = Field(alias="from")  # Using Field with alias

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "How can I improve this question?",
                "from": "user"
            }
        },
        populate_by_name=True
    )

class AnswerSchema(BaseModel):
    text: str
    is_correct: bool

class AskPayload(BaseModel):
    quiz_title: str
    quiz_description: str
    question_title: str
    question_text: str
    answers: List[AnswerSchema]
    additional_materials: str

class MutationPayload(AskPayload):
    prev_messages: List[Message]
    user_message: str

class LLMResponse(BaseModel):
    text: str