from app.rag.context import build_context
from app.schemas.repository import ChunkSearchResult


def _result(path, content, similarity, start=1, end=2):
    return ChunkSearchResult(
        file_path=path, symbol_name=None, start_line=start, end_line=end,
        similarity=similarity, content=content,
    )


def test_includes_all_chunks_when_under_budget():
    results = [_result("a.py", "x" * 10, 0.9), _result("b.py", "y" * 10, 0.8)]

    context, included = build_context(results, max_chars=1000)

    assert len(included) == 2
    assert "a.py" in context
    assert "b.py" in context


def test_drops_lowest_similarity_chunks_when_over_budget():
    results = [_result("a.py", "x" * 50, 0.9), _result("b.py", "y" * 50, 0.5)]

    context, included = build_context(results, max_chars=60)

    assert len(included) == 1
    assert included[0].file_path == "a.py"


def test_always_keeps_at_least_one_chunk_even_if_over_budget():
    results = [_result("a.py", "x" * 500, 0.9)]

    context, included = build_context(results, max_chars=10)

    assert len(included) == 1


def test_context_labels_are_numbered_and_include_line_range():
    results = [_result("a.py", "code", 0.9, start=10, end=15)]

    context, _ = build_context(results, max_chars=1000)

    assert "[1] a.py (lines 10-15)" in context


def test_empty_results_produces_empty_context():
    context, included = build_context([], max_chars=1000)

    assert context == ""
    assert included == []
