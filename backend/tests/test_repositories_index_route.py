from fastapi.testclient import TestClient

from app.api.dependencies import get_embedding_provider, get_embedding_repository, get_github_client
from app.embeddings.base import EmbeddingResult
from app.main import app
from app.models.embedding import Embedding
from app.services.exceptions import RepositoryNotIndexedError

client = TestClient(app)


class _StubGitHubClient:
    def __init__(self, tree_entries=None, contents=None):
        self._tree_entries = tree_entries or []
        self._contents = contents or {}

    def get_default_branch(self, owner, repo):
        return "main"

    def get_tree(self, owner, repo, branch):
        return self._tree_entries, False

    def get_raw_content(self, owner, repo, branch, path):
        return self._contents.get(path)


class _StubEmbeddingProvider:
    def is_available(self):
        return True, None

    def dimension(self):
        return 2

    def embed(self, texts):
        return EmbeddingResult(
            vectors=[[1.0, 0.0]] * len(texts), model="fake-model", dimension=2, duration_ms=1.0
        )


class _StubEmbeddingRepository:
    def __init__(self, rows=None, raise_not_indexed=False):
        self.rows: list[Embedding] = rows or []
        self._next_id = 1
        self._raise_not_indexed = raise_not_indexed

    def save(self, content, model, dimension, vector, source_ref=None, extra_metadata=None,
              repository=None, file_path=None, start_line=None, end_line=None, symbol_name=None):
        row = Embedding(
            id=self._next_id, content=content, model=model, dimension=dimension, vector=vector,
            repository=repository, file_path=file_path, start_line=start_line, end_line=end_line,
            symbol_name=symbol_name,
        )
        self._next_id += 1
        self.rows.append(row)
        return row

    def list_by_repository(self, repository, model, limit=5000):
        if self._raise_not_indexed:
            return []
        return [r for r in self.rows if r.repository == repository]

    def list_indexed_repositories(self):
        return [("octocat/demo", 3, "2026-01-01T00:00:00")]

    def delete_by_repository(self, repository):
        return 0


def _override(github_client=None, embedding_repository=None):
    if github_client is not None:
        app.dependency_overrides[get_github_client] = lambda: github_client
    app.dependency_overrides[get_embedding_provider] = lambda: _StubEmbeddingProvider()
    if embedding_repository is not None:
        app.dependency_overrides[get_embedding_repository] = lambda: embedding_repository


def teardown_function():
    app.dependency_overrides.pop(get_github_client, None)
    app.dependency_overrides.pop(get_embedding_provider, None)
    app.dependency_overrides.pop(get_embedding_repository, None)


def test_index_endpoint_returns_summary():
    _override(
        github_client=_StubGitHubClient(
            tree_entries=[{"path": "main.py", "type": "blob", "size": 20}],
            contents={"main.py": "def foo():\n    return 1\n"},
        ),
        embedding_repository=_StubEmbeddingRepository(),
    )

    response = client.post("/api/v1/repositories/index", json={"url": "https://github.com/octocat/demo"})

    assert response.status_code == 200
    body = response.json()
    assert body["repository"] == "octocat/demo"
    assert body["chunks_stored"] >= 1


def test_list_repositories_endpoint():
    _override(embedding_repository=_StubEmbeddingRepository())

    response = client.get("/api/v1/repositories")

    assert response.status_code == 200
    assert response.json()["repositories"][0]["repository"] == "octocat/demo"


def test_search_endpoint_returns_results():
    row = Embedding(
        id=1, content="def foo(): pass", model="fake-model", dimension=2, vector=[1.0, 0.0],
        repository="octocat/demo", file_path="a.py", start_line=1, end_line=1, symbol_name="foo",
    )
    _override(embedding_repository=_StubEmbeddingRepository(rows=[row]))

    response = client.post(
        "/api/v1/repositories/search",
        json={"repository": "octocat/demo", "query": "explain foo"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["file_path"] == "a.py"


def test_search_endpoint_returns_404_when_not_indexed():
    _override(embedding_repository=_StubEmbeddingRepository(raise_not_indexed=True))

    response = client.post(
        "/api/v1/repositories/search",
        json={"repository": "octocat/never-indexed", "query": "anything"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RepositoryNotIndexedError"


def test_search_endpoint_rejects_empty_query():
    _override(embedding_repository=_StubEmbeddingRepository())

    response = client.post(
        "/api/v1/repositories/search", json={"repository": "octocat/demo", "query": ""}
    )

    assert response.status_code == 422
