import pytest

from app.embeddings.base import EmbeddingProvider, EmbeddingResult
from app.embeddings.exceptions import EmbeddingModelUnavailableError
from app.services import embedding_service


class FakeProvider(EmbeddingProvider):
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


def test_embed_and_compare_returns_expected_shape():
    provider = FakeProvider(
        result=EmbeddingResult(
            vectors=[[1.0, 0.0], [0.0, 1.0]],
            model="fake-model",
            dimension=2,
            duration_ms=5.0,
        )
    )

    response = embedding_service.embed_and_compare(provider, ["a", "b"])

    assert response.model == "fake-model"
    assert response.dimension == 2
    assert response.count == 2
    assert len(response.embeddings) == 2


def test_embed_and_compare_computes_pairwise_similarities():
    provider = FakeProvider(
        result=EmbeddingResult(
            vectors=[[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]],
            model="fake-model",
            dimension=2,
            duration_ms=1.0,
        )
    )

    response = embedding_service.embed_and_compare(provider, ["a", "a-again", "unrelated"])

    assert len(response.similarities) == 3  # 3 choose 2
    identical_pair = next(
        p for p in response.similarities if p.text_a_index == 0 and p.text_b_index == 1
    )
    assert identical_pair.similarity == pytest.approx(1.0)

    different_pair = next(
        p for p in response.similarities if p.text_a_index == 0 and p.text_b_index == 2
    )
    assert different_pair.similarity == pytest.approx(0.0)


def test_embed_and_compare_single_text_has_no_similarities():
    provider = FakeProvider(
        result=EmbeddingResult(vectors=[[1.0, 0.0]], model="fake-model", dimension=2, duration_ms=1.0)
    )

    response = embedding_service.embed_and_compare(provider, ["only one"])

    assert response.similarities == []


def test_embed_and_compare_propagates_provider_errors():
    provider = FakeProvider(error=EmbeddingModelUnavailableError("model not loaded"))

    with pytest.raises(EmbeddingModelUnavailableError):
        embedding_service.embed_and_compare(provider, ["a"])
