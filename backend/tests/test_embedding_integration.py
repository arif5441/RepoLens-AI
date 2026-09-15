"""Real end-to-end test using the actual local embedding model (no mocks, no external service).

Slower than the unit tests (model load + encode) but doesn't depend on anything external —
sentence-transformers runs fully offline once the model is cached locally.
"""

from app.core.config import get_settings
from app.embeddings.local_provider import LocalEmbeddingProvider
from app.embeddings.similarity import cosine_similarity

settings = get_settings()


def test_real_model_dimension_matches_config():
    provider = LocalEmbeddingProvider(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        normalize=settings.embedding_normalize,
    )

    result = provider.embed(["hello world"])

    assert result.dimension == provider.dimension()
    assert len(result.vectors[0]) == result.dimension


def test_real_model_ranks_related_text_above_unrelated_text():
    """Doesn't assert exact similarity numbers (model-version-dependent) — only the ranking,
    which is the actual behavior RepoLens depends on for retrieval later."""
    provider = LocalEmbeddingProvider(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        normalize=settings.embedding_normalize,
    )

    result = provider.embed(
        [
            "calculate employee salary",
            "compute payroll amount",
            "weather forecast for tomorrow",
        ]
    )
    salary, payroll, weather = result.vectors

    related_similarity = cosine_similarity(salary, payroll)
    unrelated_similarity = cosine_similarity(salary, weather)

    assert related_similarity > unrelated_similarity
