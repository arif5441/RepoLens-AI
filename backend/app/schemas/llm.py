from pydantic import BaseModel, Field


class LLMChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    system_prompt: str | None = Field(default=None, max_length=4000)
    model: str | None = None


class LLMChatResponse(BaseModel):
    response: str
    model: str
    provider: str
    duration_ms: float


class LLMModelsResponse(BaseModel):
    models: list[str]
