from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _strip_and_validate_texts(texts: list[str]) -> list[str]:
    stripped = [text.strip() for text in texts]
    if any(not text for text in stripped):
        raise ValueError("texts must not be empty or blank")
    if any(len(text) > 2000 for text in stripped):
        raise ValueError("each text must be at most 2000 characters")
    return stripped


class EmbeddingTestRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=20)

    @field_validator("texts")
    @classmethod
    def strip_and_validate(cls, texts: list[str]) -> list[str]:
        return _strip_and_validate_texts(texts)


class SimilarityPair(BaseModel):
    text_a_index: int
    text_b_index: int
    text_a: str
    text_b: str
    similarity: float


class EmbeddingTestResponse(BaseModel):
    model: str
    dimension: int
    count: int
    embeddings: list[list[float]]
    similarities: list[SimilarityPair]
    duration_ms: float


class EmbeddingStoreRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=20)
    source_ref: str | None = Field(default=None, max_length=255)
    extra_metadata: dict | None = None

    @field_validator("texts")
    @classmethod
    def strip_and_validate(cls, texts: list[str]) -> list[str]:
        return _strip_and_validate_texts(texts)


class StoredEmbeddingSummary(BaseModel):
    id: int
    content: str
    model: str
    dimension: int
    source_ref: str | None
    created_at: datetime


class EmbeddingStoreResponse(BaseModel):
    stored: list[StoredEmbeddingSummary]
    count: int


class EmbeddingSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def strip_query(cls, query: str) -> str:
        stripped = query.strip()
        if not stripped:
            raise ValueError("query must not be empty or blank")
        return stripped


class EmbeddingSearchResult(BaseModel):
    id: int
    content: str
    source_ref: str | None
    similarity: float
    created_at: datetime


class EmbeddingSearchResponse(BaseModel):
    query: str
    model: str
    count: int
    results: list[EmbeddingSearchResult]
    duration_ms: float


class EmbeddingRecordResponse(BaseModel):
    id: int
    content: str
    model: str
    dimension: int
    source_ref: str | None
    extra_metadata: dict | None
    created_at: datetime
    updated_at: datetime
