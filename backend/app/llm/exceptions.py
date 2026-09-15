class LLMProviderError(Exception):
    """Base for all LLM provider failures. Services/routes catch this family, never httpx errors directly."""


class LLMUnavailableError(LLMProviderError):
    """The provider (Ollama) could not be reached at all."""


class LLMModelNotFoundError(LLMProviderError):
    """The provider is reachable but the configured model isn't pulled."""

    def __init__(self, model: str) -> None:
        self.model = model
        super().__init__(f"model '{model}' not found")


class LLMTimeoutError(LLMProviderError):
    """The provider took too long to respond."""


class LLMRequestError(LLMProviderError):
    """An unexpected error occurred talking to the provider."""
