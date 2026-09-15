"""File filtering rules for repository ingestion.

Deliberately a single lookup-table module rather than scattered if/else checks — extending
what's included/excluded later means editing the sets below, not hunting through the service.
"""

from pathlib import PurePosixPath

EXCLUDED_DIR_NAMES = {
    ".git",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    ".cache",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "target",
    "bin",
    "obj",
}

EXCLUDED_EXACT_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "composer.lock",
    "Pipfile.lock",
    "poetry.lock",
    "Cargo.lock",
    "Gemfile.lock",
}

EXCLUDED_FILE_SUFFIXES = (".lock", ".min.js", ".min.css", ".map")

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar",
    ".mp4", ".mov", ".avi", ".mp3", ".wav",
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar",
    ".woff", ".woff2", ".ttf", ".eot", ".otf", ".bin",
}  # fmt: skip

# extension -> language label. Extend here, not by adding checks elsewhere.
INCLUDED_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".php": "php",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cs": "csharp",
    ".go": "go",
    ".rb": "ruby",
    ".rs": "rust",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
    ".md": "markdown",
}


def detect_language(path: str) -> str | None:
    suffix = PurePosixPath(path).suffix.lower()
    return INCLUDED_EXTENSIONS.get(suffix)


def exclusion_reason(path: str, size_bytes: int, max_file_size_bytes: int) -> str | None:
    """Returns why a file would be excluded, or None if it should be included."""
    parts = PurePosixPath(path).parts
    if any(part in EXCLUDED_DIR_NAMES for part in parts[:-1]):
        return "excluded_directory"

    filename = parts[-1] if parts else path
    if filename in EXCLUDED_EXACT_FILENAMES:
        return "lockfile"
    if filename.endswith(EXCLUDED_FILE_SUFFIXES):
        return "generated_or_minified"

    suffix = PurePosixPath(path).suffix.lower()
    if suffix in BINARY_EXTENSIONS:
        return "binary_extension"
    if suffix not in INCLUDED_EXTENSIONS:
        return "unsupported_extension"

    if size_bytes > max_file_size_bytes:
        return "file_too_large"

    return None
