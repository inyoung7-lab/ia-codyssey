from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ConversationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=100)
    # Bound the whole document well below Firestore's document size limit.
    messages: list[Message] = Field(min_length=1, max_length=50)


class Conversation(ConversationInput):
    id: str
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ConversationSummary(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: AwareDatetime
    updated_at: AwareDatetime
