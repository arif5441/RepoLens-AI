from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_embedding_provider, get_embedding_repository
from app.embeddings.local_provider import LocalEmbeddingProvider
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.embedding import (
    EmbeddingRecordResponse,
    EmbeddingSearchRequest,
    EmbeddingSearchResponse,
    EmbeddingStoreRequest,
    EmbeddingStoreResponse,
    EmbeddingTestRequest,
    EmbeddingTestResponse,
)
from app.services import embedding_service

router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])


@router.post("/test", response_model=EmbeddingTestResponse)
def test_embeddings(
    request: EmbeddingTestRequest,
    provider: LocalEmbeddingProvider = Depends(get_embedding_provider),
) -> EmbeddingTestResponse:
    """Development/diagnostic endpoint: embed a handful of texts and show pairwise similarity.
    Nothing is persisted — see /store for that."""
    return embedding_service.embed_and_compare(provider, request.texts)


@router.post("/store", response_model=EmbeddingStoreResponse)
def store_embeddings(
    request: EmbeddingStoreRequest,
    provider: LocalEmbeddingProvider = Depends(get_embedding_provider),
    repository: EmbeddingRepository = Depends(get_embedding_repository),
) -> EmbeddingStoreResponse:
    """Development/diagnostic endpoint: embed texts and persist them to MySQL for later search."""
    return embedding_service.store_embeddings(
        provider, repository, request.texts, request.source_ref, request.extra_metadata
    )


@router.post("/search", response_model=EmbeddingSearchResponse)
def search_embeddings(
    request: EmbeddingSearchRequest,
    provider: LocalEmbeddingProvider = Depends(get_embedding_provider),
    repository: EmbeddingRepository = Depends(get_embedding_repository),
) -> EmbeddingSearchResponse:
    """Development/diagnostic endpoint: brute-force cosine similarity search over stored embeddings."""
    return embedding_service.search_similar(provider, repository, request.query, request.limit)


@router.get("/{embedding_id}", response_model=EmbeddingRecordResponse)
def get_embedding(
    embedding_id: int,
    repository: EmbeddingRepository = Depends(get_embedding_repository),
) -> EmbeddingRecordResponse:
    row = embedding_service.get_embedding(repository, embedding_id)
    if row is None:
        raise HTTPException(status_code=404, detail="embedding not found")
    return embedding_service.to_record_response(row)


@router.delete("/{embedding_id}", status_code=204)
def delete_embedding(
    embedding_id: int,
    repository: EmbeddingRepository = Depends(get_embedding_repository),
) -> None:
    deleted = embedding_service.delete_embedding(repository, embedding_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="embedding not found")
