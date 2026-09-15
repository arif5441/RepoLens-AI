from app.schemas.repository import ChunkSearchResult


def build_context(
    results: list[ChunkSearchResult], max_chars: int
) -> tuple[str, list[ChunkSearchResult]]:
    """Builds a labeled context block from ranked chunks, respecting a character budget.

    `results` is assumed already sorted by similarity descending (as search_repository returns
    it) — dropping from the end when over budget means dropping the least relevant chunks first.
    Always keeps at least one chunk, even if it alone exceeds the budget, so a single large but
    highly relevant chunk isn't silently discarded.
    """
    included: list[ChunkSearchResult] = []
    parts: list[str] = []
    total = 0

    for index, result in enumerate(results, start=1):
        header = f"[{index}] {result.file_path} (lines {result.start_line}-{result.end_line})"
        block = f"{header}\n{result.content}\n"
        if total + len(block) > max_chars and included:
            break
        parts.append(block)
        included.append(result)
        total += len(block)

    return "\n".join(parts), included
