class EmbeddingProviderError(Exception):
    """Base for all embedding provider failures. Services/routes catch this family."""


class EmbeddingModelUnavailableError(EmbeddingProviderError):
    """The embedding model could not be loaded (missing dependency, corrupt cache, OOM, etc)."""


class EmbeddingInputError(EmbeddingProviderError):
    """The caller passed input the provider cannot embed (empty list, blank strings)."""


class EmbeddingRequestError(EmbeddingProviderError):
    """An unexpected error occurred while generating embeddings."""
