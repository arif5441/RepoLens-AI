#!/usr/bin/env python3
"""Retrieval + answer evaluation harness.

Indexes a real small public repository, runs a curated set of questions against it, and
measures whether retrieval finds the expected file and whether RAG answers stay grounded with
correct citations. Not a CI gate (LLM calls are slow on CPU — a full run takes a few minutes) —
a report you run manually and read, same spirit as the rest of this project's "verify for real,
don't just claim it" approach.

Usage (from the backend venv, so app.* imports resolve):
    cd backend && .venv/bin/python ../evaluation/eval_retrieval.py
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.database import get_session_factory  # noqa: E402
from app.embeddings.local_provider import LocalEmbeddingProvider  # noqa: E402
from app.ingestion.github_client import GitHubClient  # noqa: E402
from app.llm.ollama_provider import OllamaProvider  # noqa: E402
from app.repositories.embedding_repository import EmbeddingRepository  # noqa: E402
from app.services import rag_service, repository_service  # noqa: E402

DATASET_PATH = Path(__file__).resolve().parent / "datasets" / "learn_python.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def main() -> None:
    settings = get_settings()
    dataset = json.loads(DATASET_PATH.read_text())

    github_client = GitHubClient(
        api_base_url=settings.github_api_base_url,
        raw_base_url=settings.github_raw_base_url,
        token=settings.github_token,
        timeout_seconds=settings.ingestion_http_timeout_seconds,
    )
    embedding_provider = LocalEmbeddingProvider(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        normalize=settings.embedding_normalize,
    )
    llm_provider = OllamaProvider(
        base_url=settings.ollama_base_url, chat_timeout_seconds=settings.ollama_chat_timeout_seconds
    )
    session = get_session_factory()()
    embedding_repository = EmbeddingRepository(session)

    print(f"Indexing {dataset['repository']} ...")
    index_result = repository_service.index_repository(
        github_client, embedding_provider, embedding_repository, dataset["repository_url"],
        max_files=settings.ingestion_max_files,
        max_file_size_bytes=settings.ingestion_max_file_size_bytes,
        max_total_size_bytes=settings.ingestion_max_total_size_bytes,
        max_lines_per_chunk=settings.chunk_max_lines,
    )
    session.commit()
    print(f"  {index_result.files_included} files, {index_result.chunks_stored} chunks stored.\n")

    retrieval_results = []
    answer_results = []

    for case in dataset["cases"]:
        question = case["question"]
        expected = case["expected_file_contains"]

        search_response = repository_service.search_repository(
            embedding_provider, embedding_repository, dataset["repository"], question, limit=5
        )
        hit = any(expected in r.file_path for r in search_response.results)
        retrieval_results.append({"question": question, "expected": expected, "hit": hit})
        print(f"[{'PASS' if hit else 'FAIL'}] retrieval: {question!r} -> expected {expected!r}")

        if case.get("run_ask"):
            started = time.monotonic()
            ask_response = rag_service.ask(
                embedding_provider, embedding_repository, llm_provider,
                dataset["repository"], question,
                top_k=settings.rag_top_k, min_similarity=settings.rag_min_similarity,
                max_context_chars=settings.rag_max_context_chars,
                llm_model=settings.ollama_model, temperature=settings.llm_temperature,
            )
            elapsed = time.monotonic() - started
            citation_correct = any(expected in c.file_path for c in ask_response.citations)
            answer_results.append({
                "question": question,
                "expected": expected,
                "grounded": ask_response.grounded,
                "citation_correct": citation_correct,
                "answer_non_empty": len(ask_response.answer.strip()) > 0,
                "elapsed_seconds": round(elapsed, 1),
            })
            status = "PASS" if ask_response.grounded and citation_correct else "FAIL"
            print(f"  [{status}] answer: grounded={ask_response.grounded} citation_correct={citation_correct} ({elapsed:.0f}s)")

    session.close()

    retrieval_hit_rate = sum(r["hit"] for r in retrieval_results) / len(retrieval_results)
    print(f"\nRetrieval hit rate: {retrieval_hit_rate:.0%} ({sum(r['hit'] for r in retrieval_results)}/{len(retrieval_results)})")

    if answer_results:
        grounded_rate = sum(a["grounded"] for a in answer_results) / len(answer_results)
        citation_rate = sum(a["citation_correct"] for a in answer_results) / len(answer_results)
        print(f"Answer grounded rate: {grounded_rate:.0%} ({sum(a['grounded'] for a in answer_results)}/{len(answer_results)})")
        print(f"Citation correctness rate: {citation_rate:.0%} ({sum(a['citation_correct'] for a in answer_results)}/{len(answer_results)})")

    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = RESULTS_DIR / f"eval_{timestamp}.json"
    output_path.write_text(json.dumps({
        "timestamp": timestamp,
        "repository": dataset["repository"],
        "embedding_model": settings.embedding_model,
        "llm_model": settings.ollama_model,
        "retrieval_results": retrieval_results,
        "retrieval_hit_rate": retrieval_hit_rate,
        "answer_results": answer_results,
    }, indent=2))
    print(f"\nResults written to {output_path.relative_to(Path(__file__).resolve().parents[1])}")


if __name__ == "__main__":
    main()
