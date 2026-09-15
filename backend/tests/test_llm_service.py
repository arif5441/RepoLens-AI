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
        self.last_model: str | None = None

    def is_available(self):
        return True, None

    def list_models(self):
        return ["phi3:mini", "llama3.2:3b"]

    def chat(self, messages, model, temperature):
        self.last_messages = messages
        self.last_model = model
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


def test_chat_uses_custom_system_prompt_when_given(settings):
    provider = FakeProvider(result=ChatResult(content="ok", model="phi3:mini", duration_ms=1.0))

    llm_service.chat(provider, settings, "hello", system_prompt="You are a pirate.")

    assert provider.last_messages[0].content == "You are a pirate."


def test_chat_uses_requested_model_override(settings):
    provider = FakeProvider(result=ChatResult(content="ok", model="llama3.2:3b", duration_ms=1.0))

    llm_service.chat(provider, settings, "hello", model="llama3.2:3b")

    assert provider.last_model == "llama3.2:3b"


def test_chat_defaults_to_configured_model_when_no_override(settings):
    provider = FakeProvider(result=ChatResult(content="ok", model=settings.ollama_model, duration_ms=1.0))

    llm_service.chat(provider, settings, "hello")

    assert provider.last_model == settings.ollama_model


def test_list_models_returns_provider_models(settings):
    provider = FakeProvider()

    response = llm_service.list_models(provider)

    assert response.models == ["phi3:mini", "llama3.2:3b"]
