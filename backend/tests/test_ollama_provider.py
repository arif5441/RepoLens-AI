from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.llm.base import ChatMessage
from app.llm.exceptions import LLMModelNotFoundError, LLMRequestError, LLMTimeoutError, LLMUnavailableError
from app.llm.ollama_provider import OllamaProvider


@pytest.fixture
def provider():
    return OllamaProvider(base_url="http://localhost:11434")


def _messages():
    return [ChatMessage(role="user", content="hi")]


def test_chat_returns_content_on_success(provider):
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {"message": {"role": "assistant", "content": "hello there"}}

    with patch("httpx.post", return_value=mock_response) as mock_post:
        result = provider.chat(_messages(), model="phi3:mini", temperature=0.3)

    assert result.content == "hello there"
    assert result.model == "phi3:mini"
    assert result.duration_ms >= 0
    mock_post.assert_called_once()


def test_chat_raises_unavailable_on_connect_error(provider):
    with patch("httpx.post", side_effect=httpx.ConnectError("refused")):
        with pytest.raises(LLMUnavailableError):
            provider.chat(_messages(), model="phi3:mini", temperature=0.3)


def test_chat_raises_timeout_on_timeout(provider):
    with patch("httpx.post", side_effect=httpx.TimeoutException("too slow")):
        with pytest.raises(LLMTimeoutError):
            provider.chat(_messages(), model="phi3:mini", temperature=0.3)


def test_chat_raises_model_not_found_on_404(provider):
    mock_response = MagicMock(status_code=404, text="model not found")

    with patch("httpx.post", return_value=mock_response):
        with pytest.raises(LLMModelNotFoundError):
            provider.chat(_messages(), model="does-not-exist", temperature=0.3)


def test_chat_raises_request_error_on_server_error(provider):
    mock_response = MagicMock(status_code=500, text="internal error")

    with patch("httpx.post", return_value=mock_response):
        with pytest.raises(LLMRequestError):
            provider.chat(_messages(), model="phi3:mini", temperature=0.3)
