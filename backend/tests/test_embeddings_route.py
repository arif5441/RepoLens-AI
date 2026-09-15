from fastapi.testclient import TestClient

from app.api.dependencies import get_embedding_provider
from app.embeddings.base import EmbeddingResult
from app.embeddings.exceptions import EmbeddingModelUnavailableError
from app.main import app

client = TestClient(app)


class _StubProvider:
    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error

    def is_available(self):
        return True, None

    def dimension(self):
        return self._result.dimension if self._result else 0

    def embed(self, texts):
        if self._error:
            raise self._error
        return self._result


def _override(provider):
    app.dependency_overrides[get_embedding_provider] = lambda: provider


def teardown_function():
    app.dependency_overrides.pop(get_embedding_provider, None)


def test_embeddings_endpoint_returns_response_on_success():
    _override(
        _StubProvider(
            result=EmbeddingResult(
                vectors=[[1.0, 0.0], [0.0, 1.0]],
                model="fake-model",
                dimension=2,
                duration_ms=5.0,
            )
        )
    )

    response = client.post("/api/v1/embeddings/test", json={"texts": ["a", "b"]})

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "fake-model"
    assert body["dimension"] == 2
    assert body["count"] == 2
    assert len(body["similarities"]) == 1


def test_embeddings_endpoint_rejects_empty_list():
    _override(_StubProvider())

    response = client.post("/api/v1/embeddings/test", json={"texts": []})

    assert response.status_code == 422


def test_embeddings_endpoint_returns_503_when_model_unavailable():
    _override(_StubProvider(error=EmbeddingModelUnavailableError("model not loaded")))

    response = client.post("/api/v1/embeddings/test", json={"texts": ["hello"]})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "EmbeddingModelUnavailableError"
