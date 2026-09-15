from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_embedding_provider,
    get_embedding_repository,
    get_github_client,
    get_ollama_provider,
)
from app.core.config import Settings, get_settings
from app.embeddings.local_provider import LocalEmbeddingProvider
from app.ingestion.github_client import GitHubClient
from app.llm.ollama_provider import OllamaProvider
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.code_intelligence import ExplainFileRequest, ExplainFileResponse
from app.schemas.ingestion import IngestionRequest, IngestionResponse
from app.schemas.rag import AskRequest, AskResponse
from app.schemas.repository import (
    ChunkSearchRequest,
    ChunkSearchResponse,
    IndexRequest,
    IndexResponse,
    RepositoryListResponse,
)
from app.services import code_intelligence_service, ingestion_service, rag_service, repository_service

router = APIRouter(prefix="/api/v1/repositories", tags=["repositories"])


@router.post("/ingest", response_model=IngestionResponse)
def ingest_repository(
    request: IngestionRequest,
    client: GitHubClient = Depends(get_github_client),
    settings: Settings = Depends(get_settings),
) -> IngestionResponse:
    """Development/diagnostic endpoint: discover and filter a public GitHub repository's
    source files. Read-only — no clone, no code execution. Doesn't chunk/embed/store —
    for that, use POST /index."""
    result = ingestion_service.ingest_repository(
        client,
        request.url,
        max_files=settings.ingestion_max_files,
        max_file_size_bytes=settings.ingestion_max_file_size_bytes,
        max_total_size_bytes=settings.ingestion_max_total_size_bytes,
    )
    return ingestion_service.to_response(result, request.include_content)


@router.post("/index", response_model=IndexResponse)
def index_repository(
    request: IndexRequest,
    github_client: GitHubClient = Depends(get_github_client),
    embedding_provider: LocalEmbeddingProvider = Depends(get_embedding_provider),
    embedding_repository: EmbeddingRepository = Depends(get_embedding_repository),
    settings: Settings = Depends(get_settings),
) -> IndexResponse:
    """Ingest + chunk + embed + store a repository, ready for search/ask. Re-indexing a
    repository that's already indexed replaces its stored chunks."""
    return repository_service.index_repository(
        github_client,
        embedding_provider,
        embedding_repository,
        request.url,
        max_files=settings.ingestion_max_files,
        max_file_size_bytes=settings.ingestion_max_file_size_bytes,
        max_total_size_bytes=settings.ingestion_max_total_size_bytes,
        max_lines_per_chunk=settings.chunk_max_lines,
    )


@router.get("", response_model=RepositoryListResponse)
def list_repositories(
    embedding_repository: EmbeddingRepository = Depends(get_embedding_repository),
) -> RepositoryListResponse:
    """Repositories that have been indexed (have stored chunks), most recently indexed first."""
    return repository_service.list_indexed_repositories(embedding_repository)


@router.post("/search", response_model=ChunkSearchResponse)
def search_repository(
    request: ChunkSearchRequest,
    embedding_provider: LocalEmbeddingProvider = Depends(get_embedding_provider),
    embedding_repository: EmbeddingRepository = Depends(get_embedding_repository),
) -> ChunkSearchResponse:
    """Semantic search over a previously indexed repository's chunks. Retrieval only — no LLM."""
    return repository_service.search_repository(
        embedding_provider,
        embedding_repository,
        request.repository,
        request.query,
        request.limit,
    )


@router.post("/ask", response_model=AskResponse)
def ask_repository(
    request: AskRequest,
    embedding_provider: LocalEmbeddingProvider = Depends(get_embedding_provider),
    embedding_repository: EmbeddingRepository = Depends(get_embedding_repository),
    llm_provider: OllamaProvider = Depends(get_ollama_provider),
    settings: Settings = Depends(get_settings),
) -> AskResponse:
    """Retrieval-augmented Q&A: retrieve relevant chunks from an indexed repository, ground the
    LLM's answer in them, return citations. Says so if there isn't enough evidence, rather than
    letting the LLM guess."""
    return rag_service.ask(
        embedding_provider,
        embedding_repository,
        llm_provider,
        request.repository,
        request.question,
        top_k=settings.rag_top_k,
        min_similarity=settings.rag_min_similarity,
        max_context_chars=settings.rag_max_context_chars,
        llm_model=settings.ollama_model,
        temperature=settings.llm_temperature,
    )


@router.post("/explain", response_model=ExplainFileResponse)
def explain_file(
    request: ExplainFileRequest,
    embedding_repository: EmbeddingRepository = Depends(get_embedding_repository),
    llm_provider: OllamaProvider = Depends(get_ollama_provider),
    settings: Settings = Depends(get_settings),
) -> ExplainFileResponse:
    """Explain one indexed file's purpose and structure, using its stored chunks as context."""
    return code_intelligence_service.explain_file(
        embedding_repository,
        llm_provider,
        request.repository,
        request.path,
        embedding_model=settings.embedding_model,
        llm_model=settings.ollama_model,
        temperature=settings.llm_temperature,
    )
