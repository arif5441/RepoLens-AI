import logging
import time

import httpx

from app.llm.base import ChatMessage, ChatResult, LLMProvider
from app.llm.exceptions import (
    LLMModelNotFoundError,
    LLMRequestError,
    LLMTimeoutError,
    LLMUnavailableError,
)

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Talks to a local Ollama server. Does not call any specific model directly."""

    def __init__(
        self, base_url: str, health_timeout_seconds: float = 3.0, chat_timeout_seconds: float = 60.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._health_timeout_seconds = health_timeout_seconds
        self._chat_timeout_seconds = chat_timeout_seconds

    def is_available(self) -> tuple[bool, str | None]:
        try:
            response = httpx.get(f"{self._base_url}/api/tags", timeout=self._health_timeout_seconds)
            response.raise_for_status()
            return True, None
        except Exception as exc:  # noqa: BLE001 — health check must never crash the endpoint
            logger.warning("Ollama health check failed: %s", exc)
            return False, "ollama unreachable"

    def list_models(self) -> list[str]:
        try:
            response = httpx.get(f"{self._base_url}/api/tags", timeout=self._health_timeout_seconds)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ollama model list failed: %s", exc)
            return []

    def chat(self, messages: list[ChatMessage], model: str, temperature: float) -> ChatResult:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }

        started = time.monotonic()
        try:
            response = httpx.post(
                f"{self._base_url}/api/chat", json=payload, timeout=self._chat_timeout_seconds
            )
        except httpx.ConnectError as exc:
            raise LLMUnavailableError("could not connect to ollama") from exc
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"ollama did not respond within {self._chat_timeout_seconds}s") from exc
        except httpx.HTTPError as exc:
            raise LLMRequestError(str(exc)) from exc

        duration_ms = (time.monotonic() - started) * 1000

        if response.status_code == 404:
            raise LLMModelNotFoundError(model)
        if response.status_code >= 400:
            raise LLMRequestError(f"ollama returned {response.status_code}: {response.text[:200]}")

        body = response.json()
        content = body.get("message", {}).get("content", "")
        return ChatResult(content=content, model=model, duration_ms=duration_ms)
