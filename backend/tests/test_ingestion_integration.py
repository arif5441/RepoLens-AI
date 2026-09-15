"""Real end-to-end test against the actual GitHub API. Skips automatically if GitHub
is unreachable (offline dev, firewall, etc) — mirrors the Ollama live-test pattern."""

import httpx
import pytest

from app.core.config import get_settings
from app.ingestion.github_client import GitHubClient
from app.services import ingestion_service

settings = get_settings()


def _github_has_rate_limit_remaining() -> bool:
    """Checks both reachability and that we haven't exhausted the unauthenticated 60/hour rate
    limit — this test suite makes real API calls, and a burst of manual live testing earlier in
    the same hour can exhaust it. Skipping in that case (rather than failing) keeps the failure
    signal meaningful: a real bug still fails the test, an exhausted quota doesn't."""
    try:
        response = httpx.get(
            f"{settings.github_api_base_url}/rate_limit",
            headers={"Authorization": f"Bearer {settings.github_token}"} if settings.github_token else {},
            timeout=3.0,
        )
        response.raise_for_status()
        return response.json()["resources"]["core"]["remaining"] > 5
    except Exception:
        return False


@pytest.mark.skipif(
    not _github_has_rate_limit_remaining(), reason="GitHub API unreachable or rate limit exhausted"
)
def test_real_ingestion_of_small_public_repository():
    client = GitHubClient(
        api_base_url=settings.github_api_base_url,
        raw_base_url=settings.github_raw_base_url,
        token=settings.github_token,
        timeout_seconds=settings.ingestion_http_timeout_seconds,
    )

    # octocat/Spoon-Knife (GitHub's own fork-demo repo): README.md (included), index.html and
    # styles.css (both excluded — not in the supported-extension allowlist). Small and stable.
    result = ingestion_service.ingest_repository(
        client,
        "https://github.com/octocat/Spoon-Knife",
        max_files=settings.ingestion_max_files,
        max_file_size_bytes=settings.ingestion_max_file_size_bytes,
        max_total_size_bytes=settings.ingestion_max_total_size_bytes,
    )

    assert result.repository == "octocat/Spoon-Knife"
    assert result.branch
    assert result.files_discovered >= 3
    assert any(f.path.lower() == "readme.md" and f.language == "markdown" for f in result.files)
    assert result.skipped_reasons.get("unsupported_extension", 0) >= 2  # index.html, styles.css


@pytest.mark.skipif(
    not _github_has_rate_limit_remaining(), reason="GitHub API unreachable or rate limit exhausted"
)
def test_real_ingestion_of_nonexistent_repository_raises_not_found():
    from app.ingestion.exceptions import RepositoryNotFoundError

    client = GitHubClient(
        api_base_url=settings.github_api_base_url,
        raw_base_url=settings.github_raw_base_url,
        timeout_seconds=settings.ingestion_http_timeout_seconds,
    )

    with pytest.raises(RepositoryNotFoundError):
        ingestion_service.ingest_repository(
            client,
            "https://github.com/octocat/this-repo-should-not-exist-xyz-123",
            max_files=100,
            max_file_size_bytes=200_000,
            max_total_size_bytes=20_000_000,
        )
