from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class ChatResult:
    content: str
    model: str
    duration_ms: float


class LLMProvider(ABC):
    """Abstraction over a local/remote LLM backend so services never call a specific runtime directly."""

    @abstractmethod
    def is_available(self) -> tuple[bool, str | None]:
        """Check whether the provider is reachable. Returns (ok, error_message)."""
        raise NotImplementedError

    @abstractmethod
    def list_models(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def chat(self, messages: list[ChatMessage], model: str, temperature: float) -> ChatResult:
        """Run one non-streaming chat completion. Raises an LLMProviderError subclass on failure."""
        raise NotImplementedError
