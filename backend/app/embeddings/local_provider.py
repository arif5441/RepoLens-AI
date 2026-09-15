import logging
import time
from functools import lru_cache

import numpy as np

from app.embeddings.base import EmbeddingProvider, EmbeddingResult
from app.embeddings.exceptions import (
    EmbeddingInputError,
    EmbeddingModelUnavailableError,
    EmbeddingRequestError,
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def _load_model(model_name: str, device: str):
    """Loads (and caches, per process) a SentenceTransformer model.

    Cached at module level — not per-request — because loading the model from
    disk takes real time; we want to pay that cost once per (model, device),
    not on every API call.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover — dependency is in requirements.txt
        raise EmbeddingModelUnavailableError("sentence-transformers is not installed") from exc

    try:
        return SentenceTransformer(model_name, device=device)
    except Exception as exc:  # noqa: BLE001 — any load failure is treated the same way
        raise EmbeddingModelUnavailableError(f"could not load model '{model_name}': {exc}") from exc


class LocalEmbeddingProvider(EmbeddingProvider):
    """Runs a local sentence-transformers model. No network calls, no external API."""

    def __init__(self, model_name: str, device: str, normalize: bool) -> None:
        self._model_name = model_name
        self._device = device
        self._normalize = normalize

    def _model(self):
        return _load_model(self._model_name, self._device)

    def is_available(self) -> tuple[bool, str | None]:
        try:
            self._model()
            return True, None
        except EmbeddingModelUnavailableError as exc:
            logger.warning("Embedding model unavailable: %s", exc)
            return False, "embedding model unavailable"

    def dimension(self) -> int:
        return self._model().get_embedding_dimension()

    def embed(self, texts: list[str]) -> EmbeddingResult:
        if not texts:
            raise EmbeddingInputError("no texts provided")
        if any(not text.strip() for text in texts):
            raise EmbeddingInputError("texts must not be blank")

        model = self._model()
        started = time.monotonic()
        try:
            vectors = model.encode(texts, normalize_embeddings=self._normalize)
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingRequestError(str(exc)) from exc
        duration_ms = (time.monotonic() - started) * 1000

        return EmbeddingResult(
            vectors=np.asarray(vectors).tolist(),
            model=self._model_name,
            dimension=self.dimension(),
            duration_ms=duration_ms,
        )
