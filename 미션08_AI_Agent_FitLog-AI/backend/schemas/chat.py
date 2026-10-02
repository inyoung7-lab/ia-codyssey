from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from backend.schemas.data import DataSummary


class ChatInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")


class ChatOutput(BaseModel):
    conversation_id: str
    answer: str
    provider: Literal["codyssey-openai-compatible"]
    model: Literal["gpt-5-mini"]
    summary: DataSummary

    tools_used: list[str] = Field(default_factory=list)
