"""Repository ingestion: GitHub URL -> filtered, normalized source files.

Function-based service (matches the existing llm_service/embedding_service style) rather than
a class — there's no per-request state to hold, so a class would just be a namespace.
"""

import logging

from app.ingestion.filters import detect_language, exclusion_reason
from app.ingestion.github_client import GitHubClient
from app.ingestion.models import IngestionResult, SourceFile
from app.ingestion.url_parser import parse_github_url
from app.schemas.ingestion import IngestionResponse, SourceFileSummary

logger = logging.getLogger(__name__)


def ingest_repository(
    client: GitHubClient,
    url: str,
    max_files: int,
    max_file_size_bytes: int,
    max_total_size_bytes: int,
) -> IngestionResult:
    owner, repo = parse_github_url(url)
    repository = f"{owner}/{repo}"

    branch = client.get_default_branch(owner, repo)
    entries, truncated = client.get_tree(owner, repo, branch)
    blobs = [entry for entry in entries if entry.get("type") == "blob"]
    files_discovered = len(blobs)

    skipped_reasons: dict[str, int] = {}

    def skip(reason: str) -> None:
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1

    # Pass 1: filter by path/extension/per-file size — cheap, no network calls yet.
    candidates: list[dict] = []
    for entry in blobs:
        path = entry["path"]
        size = entry.get("size", 0)
        reason = exclusion_reason(path, size, max_file_size_bytes)
        if reason:
            skip(reason)
        else:
            candidates.append(entry)

    # Pass 2: cap file count before spending any HTTP calls on content.
    if len(candidates) > max_files:
        for entry in candidates[max_files:]:
            skip("file_count_limit_reached")
        candidates = candidates[:max_files]

    # Pass 3: cap total content size — stop once the budget would be exceeded.
    running_total = 0
    within_budget: list[dict] = []
    for entry in candidates:
        size = entry.get("size", 0)
        if running_total + size > max_total_size_bytes:
            skip("total_size_budget_exceeded")
            continue
        running_total += size
        within_budget.append(entry)

    # Pass 4: fetch content only for files that survived every filter.
    files: list[SourceFile] = []
    total_size_bytes = 0
    for entry in within_budget:
        path = entry["path"]
        content = client.get_raw_content(owner, repo, branch, path)
        if content is None:
            skip("not_text_utf8")
            continue
        language = detect_language(path)
        size_bytes = entry.get("size", len(content.encode("utf-8")))
        files.append(
            SourceFile(
                path=path,
                language=language or "unknown",
                content=content,
                size_bytes=size_bytes,
                repository=repository,
                ref=branch,
            )
        )
        total_size_bytes += size_bytes

    logger.info(
        "Repository ingested | repository=%s branch=%s discovered=%d included=%d skipped=%d truncated=%s",
        repository,
        branch,
        files_discovered,
        len(files),
        files_discovered - len(files),
        truncated,
    )

    return IngestionResult(
        repository=repository,
        branch=branch,
        files_discovered=files_discovered,
        files_included=len(files),
        files_skipped=files_discovered - len(files),
        total_size_bytes=total_size_bytes,
        truncated=truncated,
        skipped_reasons=skipped_reasons,
        files=files,
    )


def to_response(result: IngestionResult, include_content: bool) -> IngestionResponse:
    return IngestionResponse(
        repository=result.repository,
        branch=result.branch,
        files_discovered=result.files_discovered,
        files_included=result.files_included,
        files_skipped=result.files_skipped,
        skipped_reasons=result.skipped_reasons,
        total_size_bytes=result.total_size_bytes,
        truncated=result.truncated,
        files=[
            SourceFileSummary(
                path=f.path,
                language=f.language,
                size_bytes=f.size_bytes,
                content=f.content if include_content else None,
            )
            for f in result.files
        ],
    )
