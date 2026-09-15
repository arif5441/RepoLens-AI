from fastapi.testclient import TestClient

from app.api.dependencies import get_github_client
from app.ingestion.exceptions import GitHubRateLimitedError, RepositoryNotFoundError
from app.main import app

client = TestClient(app)


class _StubGitHubClient:
    def __init__(self, tree_entries=None, contents=None, error=None):
        self._tree_entries = tree_entries or []
        self._contents = contents or {}
        self._error = error

    def get_default_branch(self, owner, repo):
        if self._error:
            raise self._error
        return "main"

    def get_tree(self, owner, repo, branch):
        return self._tree_entries, False

    def get_raw_content(self, owner, repo, branch, path):
        return self._contents.get(path)


def _override(stub):
    app.dependency_overrides[get_github_client] = lambda: stub


def teardown_function():
    app.dependency_overrides.pop(get_github_client, None)


def test_ingest_endpoint_returns_summary():
    _override(
        _StubGitHubClient(
            tree_entries=[{"path": "main.py", "type": "blob", "size": 10}],
            contents={"main.py": "print(1)"},
        )
    )

    response = client.post(
        "/api/v1/repositories/ingest", json={"url": "https://github.com/octocat/Hello-World"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository"] == "octocat/Hello-World"
    assert body["files_included"] == 1
    assert body["files"][0]["content"] is None  # include_content defaults False


def test_ingest_endpoint_includes_content_when_requested():
    _override(
        _StubGitHubClient(
            tree_entries=[{"path": "main.py", "type": "blob", "size": 10}],
            contents={"main.py": "print(1)"},
        )
    )

    response = client.post(
        "/api/v1/repositories/ingest",
        json={"url": "https://github.com/octocat/Hello-World", "include_content": True},
    )

    assert response.json()["files"][0]["content"] == "print(1)"


def test_ingest_endpoint_rejects_invalid_url():
    _override(_StubGitHubClient())

    response = client.post("/api/v1/repositories/ingest", json={"url": "not-a-github-url"})

    assert response.status_code == 400


def test_ingest_endpoint_rejects_empty_url():
    _override(_StubGitHubClient())

    response = client.post("/api/v1/repositories/ingest", json={"url": ""})

    assert response.status_code == 422


def test_ingest_endpoint_returns_404_for_missing_repository():
    _override(_StubGitHubClient(error=RepositoryNotFoundError("not found")))

    response = client.post(
        "/api/v1/repositories/ingest", json={"url": "https://github.com/octocat/does-not-exist"}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RepositoryNotFoundError"


def test_ingest_endpoint_returns_429_when_rate_limited():
    _override(_StubGitHubClient(error=GitHubRateLimitedError("rate limited")))

    response = client.post(
        "/api/v1/repositories/ingest", json={"url": "https://github.com/octocat/Hello-World"}
    )

    assert response.status_code == 429
