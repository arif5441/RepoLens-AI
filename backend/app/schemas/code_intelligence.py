from pydantic import BaseModel, Field, field_validator


class ExplainFileRequest(BaseModel):
    repository: str = Field(min_length=1, max_length=255)
    path: str = Field(min_length=1, max_length=1000)

    @field_validator("path")
    @classmethod
    def strip_path(cls, path: str) -> str:
        stripped = path.strip()
        if not stripped:
            raise ValueError("path must not be empty or blank")
        return stripped


class ExplainFileResponse(BaseModel):
    repository: str
    path: str
    explanation: str
    chunk_count: int
    model: str
    duration_ms: float
