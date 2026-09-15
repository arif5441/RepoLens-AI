import pytest
from pydantic import ValidationError

from app.schemas.embedding import EmbeddingTestRequest


def test_valid_texts_accepted():
    request = EmbeddingTestRequest(texts=["hello", "world"])
    assert request.texts == ["hello", "world"]


def test_texts_are_stripped():
    request = EmbeddingTestRequest(texts=["  hello  "])
    assert request.texts == ["hello"]


def test_empty_list_rejected():
    with pytest.raises(ValidationError):
        EmbeddingTestRequest(texts=[])


def test_blank_text_rejected():
    with pytest.raises(ValidationError):
        EmbeddingTestRequest(texts=["ok", "   "])


def test_too_many_texts_rejected():
    with pytest.raises(ValidationError):
        EmbeddingTestRequest(texts=["x"] * 21)


def test_text_too_long_rejected():
    with pytest.raises(ValidationError):
        EmbeddingTestRequest(texts=["x" * 2001])
