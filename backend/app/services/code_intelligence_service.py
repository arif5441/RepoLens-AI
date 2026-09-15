"""Code explanation: reuses stored chunks (Phase 3/5/6) + the LLM (Phase 1) to explain one
file. Deliberately narrow scope for this phase — architecture-level analysis, cross-file call
graphs, and issue detection are not implemented (see FEATURE.md for what's still pending)."""

import logging
import time

from app.llm.base import LLMProvider
from app.rag.prompts import build_explain_messages
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.code_intelligence import ExplainFileResponse
from app.services.exceptions import FileNotIndexedError

logger = logging.getLogger(__name__)


def explain_file(
    embedding_repository: EmbeddingRepository,
    llm_provider: LLMProvider,
    repository: str,
    path: str,
    embedding_model: str,
    llm_model: str,
    temperature: float,
) -> ExplainFileResponse:
    started = time.monotonic()

    chunks = embedding_repository.list_by_repository_and_path(repository, embedding_model, path)
    if not chunks:
        raise FileNotIndexedError(repository, path)

    context = "\n\n".join(f"Lines {row.start_line}-{row.end_line}:\n{row.content}" for row in chunks)
    messages = build_explain_messages(path, context)
    result = llm_provider.chat(messages, model=llm_model, temperature=temperature)

    duration_ms = (time.monotonic() - started) * 1000
    logger.info(
        "File explained | repository=%s path=%s chunks=%d duration_ms=%.0f",
        repository, path, len(chunks), duration_ms,
    )

    return ExplainFileResponse(
        repository=repository,
        path=path,
        explanation=result.content,
        chunk_count=len(chunks),
        model=result.model,
        duration_ms=result.duration_ms,
    )
