from datetime import UTC, datetime

import pytest

from app.embeddings.base import EmbeddingProvider, EmbeddingResult
from app.models.embedding import Embedding
from app.services import embedding_service


class FakeProvider(EmbeddingProvider):
    def __init__(self, result):
        self._result = result

    def is_available(self):
        return True, None

    def dimension(self):
        return self._result.dimension

    def embed(self, texts):
        return self._result


class FakeRepository:
    def __init__(self):
        self.saved: list[Embedding] = []
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
        self._next_id += 1
        self.saved.append(row)
        return row

    def get(self, embedding_id):
        return next((row for row in self.saved if row.id == embedding_id), None)

    def delete(self, embedding_id):
        row = self.get(embedding_id)
        if row is None:
            return False
        self.saved.remove(row)
        return True

    def list_by_model(self, model, limit=1000):
        return [row for row in self.saved if row.model == model][:limit]


def test_store_embeddings_saves_each_text():
    result = EmbeddingResult(
        vectors=[[1.0, 0.0], [0.0, 1.0]], model="test-model", dimension=2, duration_ms=1.0
    )
    provider = FakeProvider(result)
    repository = FakeRepository()

    response = embedding_service.store_embeddings(provider, repository, ["a", "b"])

    assert response.count == 2
    assert len(repository.saved) == 2
    assert repository.saved[0].content == "a"
    assert repository.saved[1].content == "b"


def test_store_embeddings_passes_source_ref_and_metadata():
    result = EmbeddingResult(vectors=[[1.0, 0.0]], model="test-model", dimension=2, duration_ms=1.0)
    provider = FakeProvider(result)
    repository = FakeRepository()

    embedding_service.store_embeddings(
        provider, repository, ["a"], source_ref="doc:1", extra_metadata={"k": "v"}
    )

    assert repository.saved[0].source_ref == "doc:1"
    assert repository.saved[0].extra_metadata == {"k": "v"}


def test_search_similar_ranks_by_similarity_descending():
    repository = FakeRepository()
    repository.save(content="exact match", model="test-model", dimension=2, vector=[1.0, 0.0])
    repository.save(content="opposite", model="test-model", dimension=2, vector=[-1.0, 0.0])
    repository.save(content="orthogonal", model="test-model", dimension=2, vector=[0.0, 1.0])

    query_result = EmbeddingResult(vectors=[[1.0, 0.0]], model="test-model", dimension=2, duration_ms=1.0)
    provider = FakeProvider(query_result)

    response = embedding_service.search_similar(provider, repository, "query", limit=5)

    assert response.count == 3
    assert response.results[0].content == "exact match"
    assert response.results[0].similarity == pytest.approx(1.0)
    assert response.results[-1].content == "opposite"


def test_search_similar_respects_limit():
    repository = FakeRepository()
    for i in range(5):
        repository.save(content=f"item-{i}", model="test-model", dimension=2, vector=[1.0, 0.0])

    query_result = EmbeddingResult(vectors=[[1.0, 0.0]], model="test-model", dimension=2, duration_ms=1.0)
    provider = FakeProvider(query_result)

    response = embedding_service.search_similar(provider, repository, "query", limit=2)

    assert response.count == 2


def test_get_and_delete_embedding_delegate_to_repository():
    repository = FakeRepository()
    saved = repository.save(content="x", model="test-model", dimension=2, vector=[1.0, 0.0])

    assert embedding_service.get_embedding(repository, saved.id) is saved
    assert embedding_service.delete_embedding(repository, saved.id) is True
    assert embedding_service.get_embedding(repository, saved.id) is None
