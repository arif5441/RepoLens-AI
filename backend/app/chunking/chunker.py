"""Code-aware chunking without full AST parsing.

Splits a file at lines that *look like* a function/class/method declaration, using one regex
per language family. This is a deliberate, documented tradeoff: a real per-language parser
(tree-sitter, `ast`, etc) would be far more precise, but also far more code and far more
dependencies for a portfolio-scale project. The heuristic below gets most real-world code
right (top-level and indented `def`/`class`/`function`/... declarations) and degrades safely —
anything it can't confidently detect a boundary for falls back to fixed-size line chunking,
never to a chunk that silently loses lines.

Every chunk keeps exact start/end line numbers so citations always point at real code.
"""

import re

from app.chunking.models import CodeChunk
from app.ingestion.models import SourceFile

DEFAULT_MAX_LINES = 80

# Each pattern has exactly one capturing group: the symbol's name.
_PY_PATTERNS = [
    re.compile(r"^\s*(?:async\s+)?def\s+(\w+)"),
    re.compile(r"^\s*class\s+(\w+)"),
]
_JS_PATTERNS = [
    re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)"),
    re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)"),
]
_JAVA_LIKE_PATTERNS = [
    re.compile(r"^\s*(?:public|private|protected|static|final|abstract|\s)*class\s+(\w+)"),
    re.compile(r"^\s*(?:public|private|protected|static|final|\s)*interface\s+(\w+)"),
]
_GO_PATTERNS = [re.compile(r"^func\s+(?:\([^)]*\)\s*)?(\w+)")]
_RUBY_PATTERNS = [
    re.compile(r"^\s*def\s+(\w+)"),
    re.compile(r"^\s*class\s+(\w+)"),
    re.compile(r"^\s*module\s+(\w+)"),
]
_RUST_PATTERNS = [
    re.compile(r"^\s*(?:pub\s+)?fn\s+(\w+)"),
    re.compile(r"^\s*(?:pub\s+)?struct\s+(\w+)"),
    re.compile(r"^\s*(?:pub\s+)?enum\s+(\w+)"),
]
_PHP_PATTERNS = [
    re.compile(r"^\s*(?:public|private|protected|static|\s)*function\s+(\w+)"),
    re.compile(r"^\s*class\s+(\w+)"),
]

LANGUAGE_PATTERNS: dict[str, list[re.Pattern]] = {
    "python": _PY_PATTERNS,
    "javascript": _JS_PATTERNS,
    "typescript": _JS_PATTERNS,
    "java": _JAVA_LIKE_PATTERNS,
    "csharp": _JAVA_LIKE_PATTERNS,
    "go": _GO_PATTERNS,
    "ruby": _RUBY_PATTERNS,
    "rust": _RUST_PATTERNS,
    "php": _PHP_PATTERNS,
}
# c, cpp, json, yaml, xml, markdown: no reliable single-line boundary — fixed-size chunking.


def _match_symbol(line: str, patterns: list[re.Pattern]) -> str | None:
    for pattern in patterns:
        match = pattern.match(line)
        if match:
            return match.group(1)
    return None


def _strip_trailing_blank_lines(lines: list[str], end: int) -> int:
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    return end


def chunk_source_file(source_file: SourceFile, max_lines: int = DEFAULT_MAX_LINES) -> list[CodeChunk]:
    lines = source_file.content.splitlines()
    if not lines:
        return []

    patterns = LANGUAGE_PATTERNS.get(source_file.language)
    if not patterns:
        return _chunk_by_lines(source_file, lines, max_lines)

    boundaries = [(i, _match_symbol(line, patterns)) for i, line in enumerate(lines)]
    boundary_indices = [i for i, symbol in boundaries if symbol is not None]

    if not boundary_indices:
        return _chunk_by_lines(source_file, lines, max_lines)

    segments: list[tuple[int, int, str | None]] = []
    if boundary_indices[0] > 0:
        segments.append((0, boundary_indices[0], None))  # imports/preamble before the first symbol
    for position, start in enumerate(boundary_indices):
        end = boundary_indices[position + 1] if position + 1 < len(boundary_indices) else len(lines)
        symbol = next(s for i, s in boundaries if i == start)
        segments.append((start, end, symbol))

    chunks: list[CodeChunk] = []
    chunk_index = 0
    for start, raw_end, symbol in segments:
        end = _strip_trailing_blank_lines(lines, raw_end)
        segment_lines = lines[start:end]
        if not segment_lines:
            continue

        if len(segment_lines) <= max_lines:
            chunks.append(
                _make_chunk(source_file, segment_lines, start + 1, end, chunk_index, symbol)
            )
            chunk_index += 1
        else:
            for sub_start in range(0, len(segment_lines), max_lines):
                sub_end = min(sub_start + max_lines, len(segment_lines))
                sub_lines = segment_lines[sub_start:sub_end]
                chunks.append(
                    _make_chunk(
                        source_file,
                        sub_lines,
                        start + sub_start + 1,
                        start + sub_end,
                        chunk_index,
                        symbol,
                    )
                )
                chunk_index += 1

    return chunks


def _chunk_by_lines(source_file: SourceFile, lines: list[str], max_lines: int) -> list[CodeChunk]:
    chunks: list[CodeChunk] = []
    chunk_index = 0
    for start in range(0, len(lines), max_lines):
        end = min(start + max_lines, len(lines))
        end = _strip_trailing_blank_lines(lines, end)
        segment_lines = lines[start:end]
        if not segment_lines:
            continue
        chunks.append(_make_chunk(source_file, segment_lines, start + 1, end, chunk_index, None))
        chunk_index += 1
    return chunks


def _make_chunk(
    source_file: SourceFile,
    lines: list[str],
    start_line: int,
    end_line: int,
    chunk_index: int,
    symbol: str | None,
) -> CodeChunk:
    return CodeChunk(
        repository=source_file.repository,
        ref=source_file.ref,
        path=source_file.path,
        language=source_file.language,
        content="\n".join(lines),
        start_line=start_line,
        end_line=end_line,
        chunk_index=chunk_index,
        symbol_name=symbol,
    )
