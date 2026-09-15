from fastapi.testclient import TestClient

from app.api.dependencies import get_ollama_provider
from app.llm.base import ChatResult
from app.llm.exceptions import LLMUnavailableError
from app.main import app

client = TestClient(app)


class _StubProvider:
    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error

    def is_available(self):
        return True, None

    def list_models(self):
        return []

    def chat(self, messages, model, temperature):
        if self._error:
            raise self._error
        return self._result


def _override(provider):
    app.dependency_overrides[get_ollama_provider] = lambda: provider


def teardown_function():
    app.dependency_overrides.pop(get_ollama_provider, None)


def test_chat_endpoint_returns_response_on_success():
    _override(_StubProvider(result=ChatResult(content="DI is...", model="phi3:mini", duration_ms=12.0)))

    response = client.post("/api/v1/llm/chat", json={"message": "Explain dependency injection."})

    assert response.status_code == 200
    body = response.json()
    assert body["response"] == "DI is..."
    assert body["provider"] == "ollama"
    assert body["model"] == "phi3:mini"


def test_chat_endpoint_rejects_empty_message():
    _override(_StubProvider())

    response = client.post("/api/v1/llm/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_endpoint_returns_503_when_ollama_unavailable():
    _override(_StubProvider(error=LLMUnavailableError("could not connect to ollama")))

    response = client.post("/api/v1/llm/chat", json={"message": "hello"})

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "LLMUnavailableError"
