from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    repository: str = Field(min_length=1, max_length=255)
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def strip_question(cls, question: str) -> str:
        stripped = question.strip()
        if not stripped:
            raise ValueError("question must not be empty or blank")
        return stripped


class Citation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    similarity: float
    content: str


class AskResponse(BaseModel):
    repository: str
    question: str
    answer: str
    citations: list[Citation]
    grounded: bool
    model: str
    duration_ms: float
