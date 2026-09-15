"""Ties ingestion (Phase 4) + chunking (Phase 5) + embedding storage (Phase 3) into one
'index a repository' use case, and provides repository-scoped retrieval on top of it (Phase 6).
"""

import logging
import time

from app.chunking.chunker import chunk_source_file
from app.embeddings.base import EmbeddingProvider
from app.embeddings.similarity import cosine_similarity
from app.ingestion.github_client import GitHubClient
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.repository import (
    ChunkSearchResponse,
    ChunkSearchResult,
    IndexedRepositorySummary,
    IndexResponse,
    RepositoryListResponse,
)
from app.services import ingestion_service
from app.services.exceptions import RepositoryNotIndexedError

logger = logging.getLogger(__name__)


def index_repository(
    github_client: GitHubClient,
    embedding_provider: EmbeddingProvider,
    embedding_repository: EmbeddingRepository,
    url: str,
    max_files: int,
    max_file_size_bytes: int,
    max_total_size_bytes: int,
    max_lines_per_chunk: int,
) -> IndexResponse:
    started = time.monotonic()

    ingestion_result = ingestion_service.ingest_repository(
        github_client, url, max_files, max_file_size_bytes, max_total_size_bytes
    )

    # Re-indexing replaces what's there rather than accumulating duplicates.
    embedding_repository.delete_by_repository(ingestion_result.repository)

    chunks = [
        chunk
        for source_file in ingestion_result.files
        for chunk in chunk_source_file(source_file, max_lines_per_chunk)
    ]

    chunks_stored = 0
    embedding_model = ""
    if chunks:
        embed_result = embedding_provider.embed([chunk.content for chunk in chunks])
        embedding_model = embed_result.model
        for chunk, vector in zip(chunks, embed_result.vectors):
            embedding_repository.save(
                content=chunk.content,
                model=embed_result.model,
                dimension=embed_result.dimension,
                vector=vector,
                repository=chunk.repository,
                file_path=chunk.path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                symbol_name=chunk.symbol_name,
            )
            chunks_stored += 1

    duration_ms = (time.monotonic() - started) * 1000

    logger.info(
        "Repository indexed | repository=%s files=%d chunks=%d duration_ms=%.0f",
        ingestion_result.repository,
        ingestion_result.files_included,
        chunks_stored,
        duration_ms,
    )

    return IndexResponse(
        repository=ingestion_result.repository,
        branch=ingestion_result.branch,
        files_included=ingestion_result.files_included,
        chunks_created=len(chunks),
        chunks_stored=chunks_stored,
        embedding_model=embedding_model,
        duration_ms=duration_ms,
    )


def list_indexed_repositories(embedding_repository: EmbeddingRepository) -> RepositoryListResponse:
    rows = embedding_repository.list_indexed_repositories()
    return RepositoryListResponse(
        repositories=[
            IndexedRepositorySummary(repository=repo, chunk_count=count, last_indexed_at=updated_at)
            for repo, count, updated_at in rows
        ]
    )


def search_repository(
    embedding_provider: EmbeddingProvider,
    embedding_repository: EmbeddingRepository,
    repository: str,
    query: str,
    limit: int,
) -> ChunkSearchResponse:
    started = time.monotonic()

    query_result = embedding_provider.embed([query])
    query_vector = query_result.vectors[0]

    candidates = embedding_repository.list_by_repository(repository, query_result.model)
    if not candidates:
        raise RepositoryNotIndexedError(repository)

    scored = [(row, cosine_similarity(query_vector, row.vector)) for row in candidates]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    top = scored[:limit]

    duration_ms = (time.monotonic() - started) * 1000

    return ChunkSearchResponse(
        repository=repository,
        query=query,
        count=len(top),
        results=[
            ChunkSearchResult(
                file_path=row.file_path or "",
                symbol_name=row.symbol_name,
                start_line=row.start_line or 0,
                end_line=row.end_line or 0,
                similarity=similarity,
                content=row.content,
            )
            for row, similarity in top
        ],
        duration_ms=duration_ms,
    )
