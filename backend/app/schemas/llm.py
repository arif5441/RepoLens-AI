from pydantic import BaseModel, Field


class LLMChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class LLMChatResponse(BaseModel):
    response: str
    model: str
    provider: str
    duration_ms: float
