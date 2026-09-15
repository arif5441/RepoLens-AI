from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceFile:
    path: str
    language: str
    content: str
    size_bytes: int
    repository: str  # "owner/repo"
    ref: str  # branch name (or commit SHA)


@dataclass
class IngestionResult:
    repository: str
    branch: str
    files_discovered: int
    files_included: int
    files_skipped: int
    total_size_bytes: int
    truncated: bool
    skipped_reasons: dict[str, int] = field(default_factory=dict)
    files: list[SourceFile] = field(default_factory=list)
