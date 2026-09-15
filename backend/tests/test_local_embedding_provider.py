from unittest.mock import MagicMock, patch

import pytest

from app.embeddings.exceptions import EmbeddingInputError, EmbeddingModelUnavailableError
from app.embeddings.local_provider import LocalEmbeddingProvider


@pytest.fixture
def provider():
    return LocalEmbeddingProvider(model_name="fake-model", device="cpu", normalize=True)


def _fake_model(dimension=384, vectors=None):
    model = MagicMock()
    model.get_embedding_dimension.return_value = dimension
    model.encode.return_value = vectors or [[0.1] * dimension]
    return model


def test_embed_returns_result_with_expected_shape(provider):
    fake = _fake_model(dimension=4, vectors=[[0.1, 0.2, 0.3, 0.4]])
    with patch("app.embeddings.local_provider._load_model", return_value=fake):
        result = provider.embed(["hello"])

    assert result.dimension == 4
    assert result.model == "fake-model"
    assert result.vectors == [[0.1, 0.2, 0.3, 0.4]]
    assert result.duration_ms >= 0


def test_embed_multiple_texts(provider):
    fake = _fake_model(dimension=3, vectors=[[1, 0, 0], [0, 1, 0]])
    with patch("app.embeddings.local_provider._load_model", return_value=fake):
        result = provider.embed(["a", "b"])

    assert len(result.vectors) == 2


def test_embed_rejects_empty_list(provider):
    with pytest.raises(EmbeddingInputError):
        provider.embed([])


def test_embed_rejects_blank_text(provider):
    with pytest.raises(EmbeddingInputError):
        provider.embed(["ok", "   "])


def test_is_available_false_when_model_fails_to_load(provider):
    with patch(
        "app.embeddings.local_provider._load_model",
        side_effect=EmbeddingModelUnavailableError("boom"),
    ):
        ok, error = provider.is_available()

    assert ok is False
    assert error == "embedding model unavailable"


def test_is_available_true_when_model_loads(provider):
    with patch("app.embeddings.local_provider._load_model", return_value=_fake_model()):
        ok, error = provider.is_available()

    assert ok is True
    assert error is None
