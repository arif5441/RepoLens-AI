from app.services import ingestion_service


class FakeGitHubClient:
    def __init__(self, tree_entries, truncated=False, contents=None):
        self._tree_entries = tree_entries
        self._truncated = truncated
        self._contents = contents or {}

    def get_default_branch(self, owner, repo):
        return "main"

    def get_tree(self, owner, repo, branch):
        return self._tree_entries, self._truncated

    def get_raw_content(self, owner, repo, branch, path):
        return self._contents.get(path)


def _blob(path, size):
    return {"path": path, "type": "blob", "size": size}


def test_ingest_includes_supported_files_and_skips_others():
    client = FakeGitHubClient(
        tree_entries=[
            _blob("main.py", 100),
            _blob("README.md", 50),
            _blob("node_modules/lib.js", 20),
            _blob("logo.png", 30),
            _blob("notes.txt", 10),
        ],
        contents={"main.py": "print('hi')", "README.md": "# Title"},
    )

    result = ingestion_service.ingest_repository(
        client,
        "https://github.com/octocat/Hello-World",
        max_files=100,
        max_file_size_bytes=200_000,
        max_total_size_bytes=20_000_000,
    )

    assert result.repository == "octocat/Hello-World"
    assert result.branch == "main"
    assert result.files_discovered == 5
    assert result.files_included == 2
    assert result.files_skipped == 3
    assert {f.path for f in result.files} == {"main.py", "README.md"}
    assert result.skipped_reasons["excluded_directory"] == 1
    assert result.skipped_reasons["binary_extension"] == 1
    assert result.skipped_reasons["unsupported_extension"] == 1


def test_ingest_only_processes_blob_entries_not_trees():
    client = FakeGitHubClient(
        tree_entries=[
            {"path": "src", "type": "tree", "size": 0},
            _blob("src/main.py", 10),
        ],
        contents={"src/main.py": "x = 1"},
    )

    result = ingestion_service.ingest_repository(
        client, "https://github.com/octocat/Hello-World", 100, 200_000, 20_000_000
    )

    assert result.files_discovered == 1
    assert result.files_included == 1


def test_ingest_detects_language_per_file():
    client = FakeGitHubClient(
        tree_entries=[_blob("app.ts", 10), _blob("main.go", 10)],
        contents={"app.ts": "const x = 1;", "main.go": "package main"},
    )

    result = ingestion_service.ingest_repository(
        client, "https://github.com/octocat/Hello-World", 100, 200_000, 20_000_000
    )

    languages = {f.path: f.language for f in result.files}
    assert languages == {"app.ts": "typescript", "main.go": "go"}


def test_ingest_respects_max_files_limit():
    client = FakeGitHubClient(
        tree_entries=[_blob(f"file{i}.py", 10) for i in range(5)],
        contents={f"file{i}.py": "x = 1" for i in range(5)},
    )

    result = ingestion_service.ingest_repository(
        client, "https://github.com/octocat/Hello-World", max_files=2, max_file_size_bytes=200_000,
        max_total_size_bytes=20_000_000,
    )

    assert result.files_included == 2
    assert result.skipped_reasons["file_count_limit_reached"] == 3


def test_ingest_respects_total_size_budget():
    client = FakeGitHubClient(
        tree_entries=[_blob("a.py", 600), _blob("b.py", 600)],
        contents={"a.py": "x" * 600, "b.py": "y" * 600},
    )

    result = ingestion_service.ingest_repository(
        client, "https://github.com/octocat/Hello-World", max_files=100, max_file_size_bytes=1000,
        max_total_size_bytes=1000,
    )

    assert result.files_included == 1
    assert result.skipped_reasons["total_size_budget_exceeded"] == 1


def test_ingest_skips_non_utf8_content():
    client = FakeGitHubClient(
        tree_entries=[_blob("weird.py", 10)],
        contents={"weird.py": None},  # simulates GitHubClient returning None for undecodable content
    )

    result = ingestion_service.ingest_repository(
        client, "https://github.com/octocat/Hello-World", 100, 200_000, 20_000_000
    )

    assert result.files_included == 0
    assert result.skipped_reasons["not_text_utf8"] == 1


def test_ingest_surfaces_truncated_flag_from_github():
    client = FakeGitHubClient(tree_entries=[], truncated=True)

    result = ingestion_service.ingest_repository(
        client, "https://github.com/octocat/Hello-World", 100, 200_000, 20_000_000
    )

    assert result.truncated is True


def test_to_response_omits_content_by_default():
    client = FakeGitHubClient(
        tree_entries=[_blob("main.py", 10)], contents={"main.py": "print(1)"}
    )
    result = ingestion_service.ingest_repository(
        client, "https://github.com/octocat/Hello-World", 100, 200_000, 20_000_000
    )

    response = ingestion_service.to_response(result, include_content=False)
    assert response.files[0].content is None

    response_with_content = ingestion_service.to_response(result, include_content=True)
    assert response_with_content.files[0].content == "print(1)"
