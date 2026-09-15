from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.ingestion.exceptions import (
    GitHubRateLimitedError,
    GitHubRequestError,
    RepositoryNotFoundError,
)
from app.ingestion.github_client import GitHubClient


@pytest.fixture
def client():
    return GitHubClient(
        api_base_url="https://api.github.com",
        raw_base_url="https://raw.githubusercontent.com",
    )


def test_get_default_branch_returns_branch_name(client):
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {"default_branch": "main"}

    with patch("httpx.get", return_value=mock_response):
        assert client.get_default_branch("octocat", "Hello-World") == "main"


def test_get_default_branch_raises_not_found_on_404(client):
    mock_response = MagicMock(status_code=404)

    with patch("httpx.get", return_value=mock_response):
        with pytest.raises(RepositoryNotFoundError):
            client.get_default_branch("octocat", "does-not-exist")


def test_get_default_branch_raises_rate_limited_on_403(client):
    mock_response = MagicMock(status_code=403)

    with patch("httpx.get", return_value=mock_response):
        with pytest.raises(GitHubRateLimitedError):
            client.get_default_branch("octocat", "Hello-World")


def test_get_default_branch_raises_request_error_on_timeout(client):
    with patch("httpx.get", side_effect=httpx.TimeoutException("slow")):
        with pytest.raises(GitHubRequestError):
            client.get_default_branch("octocat", "Hello-World")


def test_get_tree_returns_entries_and_truncated_flag(client):
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {
        "tree": [{"path": "README.md", "type": "blob", "size": 10}],
        "truncated": False,
    }

    with patch("httpx.get", return_value=mock_response):
        entries, truncated = client.get_tree("octocat", "Hello-World", "main")

    assert entries == [{"path": "README.md", "type": "blob", "size": 10}]
    assert truncated is False


def test_get_raw_content_returns_decoded_text(client):
    mock_response = MagicMock(status_code=200)
    mock_response.content = b"print('hello')"

    with patch("httpx.get", return_value=mock_response):
        content = client.get_raw_content("octocat", "Hello-World", "main", "hello.py")

    assert content == "print('hello')"


def test_get_raw_content_returns_none_for_non_utf8(client):
    mock_response = MagicMock(status_code=200)
    mock_response.content = b"\xff\xfe\x00\x01binary-garbage"

    with patch("httpx.get", return_value=mock_response):
        content = client.get_raw_content("octocat", "Hello-World", "main", "weird.py")

    assert content is None


def test_get_raw_content_raises_not_found_on_404(client):
    mock_response = MagicMock(status_code=404)

    with patch("httpx.get", return_value=mock_response):
        with pytest.raises(RepositoryNotFoundError):
            client.get_raw_content("octocat", "Hello-World", "main", "missing.py")


def test_token_sets_authorization_header():
    client = GitHubClient(
        api_base_url="https://api.github.com",
        raw_base_url="https://raw.githubusercontent.com",
        token="secret-token",
    )
    assert client._headers()["Authorization"] == "Bearer secret-token"


def test_no_token_omits_authorization_header(client):
    assert "Authorization" not in client._headers()
