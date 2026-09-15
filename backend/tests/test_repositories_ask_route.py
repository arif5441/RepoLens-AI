from fastapi.testclient import TestClient

from app.api.dependencies import get_embedding_provider, get_embedding_repository, get_ollama_provider
from app.embeddings.base import EmbeddingResult
from app.llm.base import ChatResult
from app.main import app
from app.models.embedding import Embedding

client = TestClient(app)


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
    def __init__(self, rows=None):
        self.rows = rows or []

    def list_by_repository(self, repository, model, limit=5000):
        return [r for r in self.rows if r.repository == repository]


class _StubLLMProvider:
    def is_available(self):
        return True, None

    def list_models(self):
        return []

    def chat(self, messages, model, temperature):
        return ChatResult(content="DI is a design pattern [1].", model=model, duration_ms=5.0)


def _override(rows=None):
    app.dependency_overrides[get_embedding_provider] = lambda: _StubEmbeddingProvider()
    app.dependency_overrides[get_embedding_repository] = lambda: _StubEmbeddingRepository(rows)
    app.dependency_overrides[get_ollama_provider] = lambda: _StubLLMProvider()


def teardown_function():
    app.dependency_overrides.pop(get_embedding_provider, None)
    app.dependency_overrides.pop(get_embedding_repository, None)
    app.dependency_overrides.pop(get_ollama_provider, None)


def test_ask_endpoint_returns_grounded_answer():
    row = Embedding(
        id=1, content="class Container: ...", model="fake-model", dimension=2, vector=[1.0, 0.0],
        repository="octocat/demo", file_path="di.py", start_line=1, end_line=10, symbol_name="Container",
    )
    _override(rows=[row])

    response = client.post(
        "/api/v1/repositories/ask",
        json={"repository": "octocat/demo", "question": "What is dependency injection?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True
    assert body["citations"][0]["file_path"] == "di.py"


def test_ask_endpoint_returns_404_when_repository_not_indexed():
    _override(rows=[])

    response = client.post(
        "/api/v1/repositories/ask",
        json={"repository": "octocat/never-indexed", "question": "anything?"},
    )

    assert response.status_code == 404


def test_ask_endpoint_rejects_empty_question():
    _override(rows=[])

    response = client.post(
        "/api/v1/repositories/ask", json={"repository": "octocat/demo", "question": ""}
    )

    assert response.status_code == 422
