from dataclasses import dataclass


@dataclass(frozen=True)
class CodeChunk:
    repository: str
    ref: str
    path: str
    language: str
    content: str
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive
    chunk_index: int  # position within the file, 0-based
    symbol_name: str | None  # function/class name if a boundary was detected, else None
