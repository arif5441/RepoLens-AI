import pytest

from app.core.config import get_settings
from app.llm.base import ChatMessage, ChatResult, LLMProvider
from app.llm.exceptions import LLMUnavailableError
from app.services import llm_service


class FakeProvider(LLMProvider):
    def __init__(self, result: ChatResult | None = None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self.last_messages: list[ChatMessage] | None = None

    def is_available(self):
        return True, None

    def list_models(self):
        return []

    def chat(self, messages, model, temperature):
        self.last_messages = messages
        if self._error:
            raise self._error
        return self._result


@pytest.fixture
def settings():
    return get_settings()


def test_chat_returns_structured_response(settings):
    provider = FakeProvider(result=ChatResult(content="DI is...", model="phi3:mini", duration_ms=42.0))

    response = llm_service.chat(provider, settings, "Explain dependency injection.")

    assert response.response == "DI is..."
    assert response.model == "phi3:mini"
    assert response.provider == "ollama"
    assert response.duration_ms == 42.0


def test_chat_builds_system_and_user_messages(settings):
    provider = FakeProvider(result=ChatResult(content="ok", model="phi3:mini", duration_ms=1.0))

    llm_service.chat(provider, settings, "hello")

    assert provider.last_messages is not None
    roles = [m.role for m in provider.last_messages]
    assert roles == ["system", "user"]
    assert provider.last_messages[1].content == "hello"


def test_chat_propagates_provider_errors(settings):
    provider = FakeProvider(error=LLMUnavailableError("could not connect to ollama"))

    with pytest.raises(LLMUnavailableError):
        llm_service.chat(provider, settings, "hello")
