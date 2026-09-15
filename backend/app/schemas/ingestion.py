from pydantic import BaseModel, Field, field_validator


class IngestionRequest(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    include_content: bool = False

    @field_validator("url")
    @classmethod
    def strip_url(cls, url: str) -> str:
        stripped = url.strip()
        if not stripped:
            raise ValueError("url must not be empty or blank")
        return stripped


class SourceFileSummary(BaseModel):
    path: str
    language: str
    size_bytes: int
    content: str | None = None


class IngestionResponse(BaseModel):
    repository: str
    branch: str
    files_discovered: int
    files_included: int
    files_skipped: int
    skipped_reasons: dict[str, int]
    total_size_bytes: int
    truncated: bool
    files: list[SourceFileSummary]
