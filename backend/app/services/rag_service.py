"""Question → retrieve chunks → build context → LLM → grounded answer with citations.

This is the phase that finally connects the LLM path (Phase 1) and the embedding/retrieval
path (Phases 2-6) — until now they were two separate, unconnected capabilities.
"""

import logging

from app.embeddings.base import EmbeddingProvider
from app.llm.base import LLMProvider
from app.rag.context import build_context
from app.rag.prompts import build_rag_messages
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.rag import AskResponse, Citation
from app.services import repository_service

logger = logging.getLogger(__name__)

INSUFFICIENT_EVIDENCE_ANSWER = (
    "I could not find enough evidence in the indexed repository to answer this question. "
    "Try rephrasing, or make sure the repository has been indexed and actually contains "
    "relevant code."
)


def ask(
    embedding_provider: EmbeddingProvider,
    embedding_repository: EmbeddingRepository,
    llm_provider: LLMProvider,
    repository: str,
    question: str,
    top_k: int,
    min_similarity: float,
    max_context_chars: int,
    llm_model: str,
    temperature: float,
) -> AskResponse:
    search_response = repository_service.search_repository(
        embedding_provider, embedding_repository, repository, question, top_k
    )  # raises RepositoryNotIndexedError if nothing is stored for this repository

    relevant = [r for r in search_response.results if r.similarity >= min_similarity]

    if not relevant:
        logger.info(
            "RAG: no evidence above threshold | repository=%s min_similarity=%.2f candidates=%d",
            repository,
            min_similarity,
            len(search_response.results),
        )
        return AskResponse(
            repository=repository,
            question=question,
            answer=INSUFFICIENT_EVIDENCE_ANSWER,
            citations=[],
            grounded=False,
            model=llm_model,
            duration_ms=search_response.duration_ms,
        )

    context, included = build_context(relevant, max_context_chars)
    messages = build_rag_messages(question, context)
    result = llm_provider.chat(messages, model=llm_model, temperature=temperature)

    logger.info(
        "RAG answer generated | repository=%s chunks_used=%d duration_ms=%.0f",
        repository,
        len(included),
        result.duration_ms,
    )

    return AskResponse(
        repository=repository,
        question=question,
        answer=result.content,
        citations=[
            Citation(
                file_path=r.file_path,
                start_line=r.start_line,
                end_line=r.end_line,
                similarity=r.similarity,
                content=r.content,
            )
            for r in included
        ],
        grounded=True,
        model=result.model,
        duration_ms=result.duration_ms,
    )
