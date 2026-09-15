from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: list[list[float]]
    model: str
    dimension: int
    duration_ms: float


class EmbeddingProvider(ABC):
    """Abstraction over a local/remote embedding backend so services never call a specific library directly."""

    @abstractmethod
    def is_available(self) -> tuple[bool, str | None]:
        """Check whether the provider's model can be loaded. Returns (ok, error_message)."""
        raise NotImplementedError

    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed(self, texts: list[str]) -> EmbeddingResult:
        """Embed one or more texts. Raises an EmbeddingProviderError subclass on failure."""
        raise NotImplementedError
