from fastapi.testclient import TestClient

from app.api.dependencies import get_embedding_repository, get_ollama_provider
from app.llm.base import ChatResult
from app.main import app
from app.models.embedding import Embedding

client = TestClient(app)


class _StubLLMProvider:
    def is_available(self):
        return True, None

    def list_models(self):
        return []

    def chat(self, messages, model, temperature):
        return ChatResult(content="This file implements X.", model=model, duration_ms=2.0)


class _StubEmbeddingRepository:
    def __init__(self, rows=None):
        self.rows = rows or []

    def list_by_repository_and_path(self, repository, model, file_path):
        return [r for r in self.rows if r.repository == repository and r.file_path == file_path]


def _override(rows=None):
    app.dependency_overrides[get_embedding_repository] = lambda: _StubEmbeddingRepository(rows)
    app.dependency_overrides[get_ollama_provider] = lambda: _StubLLMProvider()


def teardown_function():
    app.dependency_overrides.pop(get_embedding_repository, None)
    app.dependency_overrides.pop(get_ollama_provider, None)


def test_explain_endpoint_returns_explanation():
    row = Embedding(
        id=1, content="class Foo: pass", model="m", dimension=2, vector=[1.0, 0.0],
        repository="octocat/demo", file_path="main.py", start_line=1, end_line=1,
    )
    _override(rows=[row])

    response = client.post(
        "/api/v1/repositories/explain", json={"repository": "octocat/demo", "path": "main.py"}
    )

    assert response.status_code == 200
    assert response.json()["explanation"] == "This file implements X."


def test_explain_endpoint_returns_404_for_unindexed_file():
    _override(rows=[])

    response = client.post(
        "/api/v1/repositories/explain", json={"repository": "octocat/demo", "path": "missing.py"}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FileNotIndexedError"


def test_explain_endpoint_rejects_empty_path():
    _override(rows=[])

    response = client.post(
        "/api/v1/repositories/explain", json={"repository": "octocat/demo", "path": ""}
    )

    assert response.status_code == 422
