from pydantic import BaseModel, Field, field_validator


class IndexRequest(BaseModel):
    url: str = Field(min_length=1, max_length=500)

    @field_validator("url")
    @classmethod
    def strip_url(cls, url: str) -> str:
        stripped = url.strip()
        if not stripped:
            raise ValueError("url must not be empty or blank")
        return stripped


class IndexResponse(BaseModel):
    repository: str
    branch: str
    files_included: int
    chunks_created: int
    chunks_stored: int
    embedding_model: str
    duration_ms: float


class IndexedRepositorySummary(BaseModel):
    repository: str
    chunk_count: int
    last_indexed_at: str


class RepositoryListResponse(BaseModel):
    repositories: list[IndexedRepositorySummary]


class ChunkSearchRequest(BaseModel):
    repository: str = Field(min_length=1, max_length=255)
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def strip_query(cls, query: str) -> str:
        stripped = query.strip()
        if not stripped:
            raise ValueError("query must not be empty or blank")
        return stripped


class ChunkSearchResult(BaseModel):
    file_path: str
    symbol_name: str | None
    start_line: int
    end_line: int
    similarity: float
    content: str


class ChunkSearchResponse(BaseModel):
    repository: str
    query: str
    count: int
    results: list[ChunkSearchResult]
    duration_ms: float
