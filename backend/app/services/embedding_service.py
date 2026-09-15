import logging
import time

from app.embeddings.base import EmbeddingProvider
from app.embeddings.exceptions import EmbeddingProviderError
from app.embeddings.similarity import cosine_similarity
from app.models.embedding import Embedding
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.embedding import (
    EmbeddingRecordResponse,
    EmbeddingSearchResponse,
    EmbeddingSearchResult,
    EmbeddingStoreResponse,
    EmbeddingTestResponse,
    SimilarityPair,
    StoredEmbeddingSummary,
)

logger = logging.getLogger(__name__)


def embed_and_compare(provider: EmbeddingProvider, texts: list[str]) -> EmbeddingTestResponse:
    """Diagnostic use case: embed a handful of texts and compare them in-memory. Nothing is stored."""
    try:
        result = provider.embed(texts)
    except EmbeddingProviderError:
        logger.warning("Embedding generation failed | text_count=%d", len(texts))
        raise

    similarities = [
        SimilarityPair(
            text_a_index=i,
            text_b_index=j,
            text_a=texts[i],
            text_b=texts[j],
            similarity=cosine_similarity(result.vectors[i], result.vectors[j]),
        )
        for i in range(len(texts))
        for j in range(i + 1, len(texts))
    ]

    logger.info(
        "Embedding generation succeeded | model=%s dimension=%d text_count=%d duration_ms=%.0f",
        result.model,
        result.dimension,
        len(texts),
        result.duration_ms,
    )

    return EmbeddingTestResponse(
        model=result.model,
        dimension=result.dimension,
        count=len(texts),
        embeddings=result.vectors,
        similarities=similarities,
        duration_ms=result.duration_ms,
    )


def store_embeddings(
    provider: EmbeddingProvider,
    repository: EmbeddingRepository,
    texts: list[str],
    source_ref: str | None = None,
    extra_metadata: dict | None = None,
) -> EmbeddingStoreResponse:
    """Embed each text and persist it. Used to build up a searchable set of vectors."""
    result = provider.embed(texts)

    stored = [
        repository.save(
            content=text,
            model=result.model,
            dimension=result.dimension,
            vector=vector,
            source_ref=source_ref,
            extra_metadata=extra_metadata,
        )
        for text, vector in zip(texts, result.vectors)
    ]

    logger.info(
        "Embeddings stored | model=%s dimension=%d count=%d", result.model, result.dimension, len(stored)
    )

    return EmbeddingStoreResponse(
        stored=[
            StoredEmbeddingSummary(
                id=row.id,
                content=row.content,
                model=row.model,
                dimension=row.dimension,
                source_ref=row.source_ref,
                created_at=row.created_at,
            )
            for row in stored
        ],
        count=len(stored),
    )


def search_similar(
    provider: EmbeddingProvider,
    repository: EmbeddingRepository,
    query: str,
    limit: int,
) -> EmbeddingSearchResponse:
    """Brute-force cosine similarity search: embed the query, compare against every stored
    vector for the same model (vectors from different models aren't comparable), rank, return
    the top N. See docs/architecture/overview.md for why this is brute-force, not ANN indexed."""
    started = time.monotonic()

    result = provider.embed([query])
    query_vector = result.vectors[0]

    candidates = repository.list_by_model(result.model)
    scored = [
        (candidate, cosine_similarity(query_vector, candidate.vector)) for candidate in candidates
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    top = scored[:limit]

    duration_ms = (time.monotonic() - started) * 1000

    logger.info(
        "Similarity search | model=%s candidates=%d returned=%d duration_ms=%.0f",
        result.model,
        len(candidates),
        len(top),
        duration_ms,
    )

    return EmbeddingSearchResponse(
        query=query,
        model=result.model,
        count=len(top),
        results=[
            EmbeddingSearchResult(
                id=candidate.id,
                content=candidate.content,
                source_ref=candidate.source_ref,
                similarity=similarity,
                created_at=candidate.created_at,
            )
            for candidate, similarity in top
        ],
        duration_ms=duration_ms,
    )


def get_embedding(repository: EmbeddingRepository, embedding_id: int) -> Embedding | None:
    return repository.get(embedding_id)


def delete_embedding(repository: EmbeddingRepository, embedding_id: int) -> bool:
    return repository.delete(embedding_id)


def to_record_response(row: Embedding) -> EmbeddingRecordResponse:
    return EmbeddingRecordResponse(
        id=row.id,
        content=row.content,
        model=row.model,
        dimension=row.dimension,
        source_ref=row.source_ref,
        extra_metadata=row.extra_metadata,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
