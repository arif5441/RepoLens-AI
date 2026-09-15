from app.ingestion.filters import detect_language, exclusion_reason

MAX_SIZE = 200_000


def test_included_source_file_has_no_exclusion_reason():
    assert exclusion_reason("src/app/main.py", 1000, MAX_SIZE) is None


def test_nested_directory_source_file_included():
    assert exclusion_reason("app/services/deep/nested/module.py", 500, MAX_SIZE) is None


def test_excludes_git_directory():
    assert exclusion_reason(".git/config", 100, MAX_SIZE) == "excluded_directory"


def test_excludes_node_modules():
    assert exclusion_reason("node_modules/lodash/index.js", 100, MAX_SIZE) == "excluded_directory"


def test_excludes_vendor_dist_build_coverage():
    assert exclusion_reason("vendor/pkg/file.php", 100, MAX_SIZE) == "excluded_directory"
    assert exclusion_reason("dist/bundle.js", 100, MAX_SIZE) == "excluded_directory"
    assert exclusion_reason("build/output.js", 100, MAX_SIZE) == "excluded_directory"
    assert exclusion_reason("coverage/report.js", 100, MAX_SIZE) == "excluded_directory"


def test_excludes_lockfiles():
    assert exclusion_reason("package-lock.json", 100, MAX_SIZE) == "lockfile"
    assert exclusion_reason("poetry.lock", 100, MAX_SIZE) == "lockfile"


def test_excludes_binary_extensions():
    assert exclusion_reason("assets/logo.png", 100, MAX_SIZE) == "binary_extension"
    assert exclusion_reason("archive.zip", 100, MAX_SIZE) == "binary_extension"
    assert exclusion_reason("video.mp4", 100, MAX_SIZE) == "binary_extension"


def test_excludes_unsupported_extensions():
    assert exclusion_reason("notes.txt", 100, MAX_SIZE) == "unsupported_extension"
    assert exclusion_reason("Makefile", 100, MAX_SIZE) == "unsupported_extension"


def test_excludes_files_over_size_limit():
    assert exclusion_reason("big.py", MAX_SIZE + 1, MAX_SIZE) == "file_too_large"


def test_includes_file_at_exact_size_limit():
    assert exclusion_reason("exact.py", MAX_SIZE, MAX_SIZE) is None


def test_detect_language_for_supported_extensions():
    assert detect_language("main.py") == "python"
    assert detect_language("app.ts") == "typescript"
    assert detect_language("Component.tsx") == "typescript"
    assert detect_language("README.md") == "markdown"
    assert detect_language("config.yaml") == "yaml"


def test_detect_language_returns_none_for_unsupported():
    assert detect_language("notes.txt") is None
    assert detect_language("Makefile") is None
