from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import get_embedding_provider, get_embedding_repository
from app.embeddings.base import EmbeddingResult
from app.main import app
from app.models.embedding import Embedding

client = TestClient(app)


class _StubProvider:
    def __init__(self, result):
        self._result = result

    def is_available(self):
        return True, None

    def dimension(self):
        return self._result.dimension

    def embed(self, texts):
        return self._result


class _StubRepository:
    def __init__(self):
        self.rows: dict[int, Embedding] = {}
        self._next_id = 1

    def save(self, content, model, dimension, vector, source_ref=None, extra_metadata=None):
        row = Embedding(
            id=self._next_id,
            content=content,
            model=model,
            dimension=dimension,
            vector=vector,
            source_ref=source_ref,
            extra_metadata=extra_metadata,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.rows[row.id] = row
        self._next_id += 1
        return row

    def get(self, embedding_id):
        return self.rows.get(embedding_id)

    def delete(self, embedding_id):
        return self.rows.pop(embedding_id, None) is not None

    def list_by_model(self, model, limit=1000):
        return [r for r in self.rows.values() if r.model == model][:limit]


def _override(provider=None, repository=None):
    if provider is not None:
        app.dependency_overrides[get_embedding_provider] = lambda: provider
    if repository is not None:
        app.dependency_overrides[get_embedding_repository] = lambda: repository


def teardown_function():
    app.dependency_overrides.pop(get_embedding_provider, None)
    app.dependency_overrides.pop(get_embedding_repository, None)


def test_store_endpoint_persists_and_returns_summary():
    result = EmbeddingResult(vectors=[[1.0, 0.0]], model="test-model", dimension=2, duration_ms=1.0)
    repository = _StubRepository()
    _override(provider=_StubProvider(result), repository=repository)

    response = client.post("/api/v1/embeddings/store", json={"texts": ["hello"]})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["stored"][0]["content"] == "hello"
    assert len(repository.rows) == 1


def test_search_endpoint_returns_ranked_results():
    repository = _StubRepository()
    repository.save(content="exact", model="test-model", dimension=2, vector=[1.0, 0.0])
    repository.save(content="unrelated", model="test-model", dimension=2, vector=[0.0, 1.0])
    result = EmbeddingResult(vectors=[[1.0, 0.0]], model="test-model", dimension=2, duration_ms=1.0)
    _override(provider=_StubProvider(result), repository=repository)

    response = client.post("/api/v1/embeddings/search", json={"query": "find exact", "limit": 5})

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["content"] == "exact"


def test_search_endpoint_rejects_empty_query():
    repository = _StubRepository()
    result = EmbeddingResult(vectors=[[1.0, 0.0]], model="test-model", dimension=2, duration_ms=1.0)
    _override(provider=_StubProvider(result), repository=repository)

    response = client.post("/api/v1/embeddings/search", json={"query": ""})

    assert response.status_code == 422


def test_get_endpoint_returns_404_for_missing_id():
    _override(repository=_StubRepository())

    response = client.get("/api/v1/embeddings/999999")

    assert response.status_code == 404


def test_get_endpoint_returns_stored_record():
    repository = _StubRepository()
    saved = repository.save(content="hi", model="test-model", dimension=2, vector=[1.0, 0.0])
    _override(repository=repository)

    response = client.get(f"/api/v1/embeddings/{saved.id}")

    assert response.status_code == 200
    assert response.json()["content"] == "hi"


def test_delete_endpoint_removes_record():
    repository = _StubRepository()
    saved = repository.save(content="bye", model="test-model", dimension=2, vector=[1.0, 0.0])
    _override(repository=repository)

    response = client.delete(f"/api/v1/embeddings/{saved.id}")

    assert response.status_code == 204
    assert repository.get(saved.id) is None


def test_delete_endpoint_returns_404_for_missing_id():
    _override(repository=_StubRepository())

    response = client.delete("/api/v1/embeddings/999999")

    assert response.status_code == 404
