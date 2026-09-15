from fastapi.testclient import TestClient

from app.api.dependencies import get_embedding_provider, get_embedding_repository
from app.embeddings.base import EmbeddingResult
from app.main import app
from app.repositories.exceptions import RepositoryError

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


class _FailingRepository:
    def save(self, *args, **kwargs):
        raise RepositoryError("could not save embedding: connection to 'repolens'@'localhost' lost")

    def get(self, embedding_id):
        raise RepositoryError("boom")

    def delete(self, embedding_id):
        raise RepositoryError("boom")

    def list_by_model(self, model, limit=1000):
        raise RepositoryError("boom")


def teardown_function():
    app.dependency_overrides.pop(get_embedding_provider, None)
    app.dependency_overrides.pop(get_embedding_repository, None)


def test_store_endpoint_returns_503_on_database_error_without_leaking_detail():
    result = EmbeddingResult(vectors=[[1.0, 0.0]], model="test-model", dimension=2, duration_ms=1.0)
    app.dependency_overrides[get_embedding_provider] = lambda: _StubProvider(result)
    app.dependency_overrides[get_embedding_repository] = lambda: _FailingRepository()

    response = client.post("/api/v1/embeddings/store", json={"texts": ["hello"]})

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "DatabaseError"
    assert body["error"]["message"] == "database unavailable"
    assert "repolens" not in body["error"]["message"]
    assert "localhost" not in body["error"]["message"]
