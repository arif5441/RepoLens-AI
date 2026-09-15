import logging

import httpx

from app.ingestion.exceptions import (
    GitHubRateLimitedError,
    GitHubRequestError,
    RepositoryNotFoundError,
)

logger = logging.getLogger(__name__)


class GitHubClient:
    """Read-only access to GitHub's REST API + raw content CDN. No git, no local clone,
    no code execution — every operation here is a plain HTTP GET."""

    def __init__(
        self,
        api_base_url: str,
        raw_base_url: str,
        token: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._api_base_url = api_base_url.rstrip("/")
        self._raw_base_url = raw_base_url.rstrip("/")
        self._token = token
        self._timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _get_json(self, url: str) -> dict:
        try:
            response = httpx.get(url, headers=self._headers(), timeout=self._timeout_seconds)
        except httpx.TimeoutException as exc:
            raise GitHubRequestError(f"GitHub request timed out: {url}") from exc
        except httpx.HTTPError as exc:
            raise GitHubRequestError(str(exc)) from exc

        if response.status_code == 404:
            raise RepositoryNotFoundError("repository not found or not accessible")
        if response.status_code in (403, 429):
            raise GitHubRateLimitedError("GitHub API rate limit exceeded — try again later")
        if response.status_code >= 400:
            raise GitHubRequestError(f"GitHub returned {response.status_code} for {url}")

        return response.json()

    def get_default_branch(self, owner: str, repo: str) -> str:
        data = self._get_json(f"{self._api_base_url}/repos/{owner}/{repo}")
        return data["default_branch"]

    def get_tree(self, owner: str, repo: str, branch: str) -> tuple[list[dict], bool]:
        """Returns (entries, truncated). Each entry has 'path', 'type' ('blob'/'tree'), 'size'."""
        data = self._get_json(
            f"{self._api_base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        )
        return data.get("tree", []), bool(data.get("truncated", False))

    def get_raw_content(self, owner: str, repo: str, branch: str, path: str) -> str | None:
        """Returns the file's text content, or None if it isn't valid UTF-8 text
        (i.e. it's binary despite having a text-like extension)."""
        url = f"{self._raw_base_url}/{owner}/{repo}/{branch}/{path}"
        try:
            response = httpx.get(url, timeout=self._timeout_seconds)
        except httpx.TimeoutException as exc:
            raise GitHubRequestError(f"GitHub request timed out: {url}") from exc
        except httpx.HTTPError as exc:
            raise GitHubRequestError(str(exc)) from exc

        if response.status_code == 404:
            raise RepositoryNotFoundError(f"file not found: {path}")
        if response.status_code in (403, 429):
            raise GitHubRateLimitedError("GitHub API rate limit exceeded — try again later")
        if response.status_code >= 400:
            raise GitHubRequestError(f"GitHub returned {response.status_code} for {path}")

        try:
            return response.content.decode("utf-8")
        except UnicodeDecodeError:
            logger.info("Skipping non-UTF-8 file: %s", path)
            return None
