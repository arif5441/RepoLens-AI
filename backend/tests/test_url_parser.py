import pytest

from app.ingestion.exceptions import InvalidRepositoryUrlError
from app.ingestion.url_parser import parse_github_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/octocat/Hello-World", ("octocat", "Hello-World")),
        ("https://github.com/octocat/Hello-World/", ("octocat", "Hello-World")),
        ("https://github.com/octocat/Hello-World.git", ("octocat", "Hello-World")),
        ("https://www.github.com/octocat/Hello-World", ("octocat", "Hello-World")),
        ("http://github.com/octocat/Hello-World", ("octocat", "Hello-World")),
        ("  https://github.com/octocat/Hello-World  ", ("octocat", "Hello-World")),
        ("https://github.com/my-org/my.repo-name_2", ("my-org", "my.repo-name_2")),
    ],
)
def test_parses_valid_github_urls(url, expected):
    assert parse_github_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not a url",
        "https://gitlab.com/owner/repo",
        "https://github.com/owner",
        "https://github.com/",
        "github.com/owner/repo",
        "ftp://github.com/owner/repo",
        "https://github.com/owner/repo/extra/path",
    ],
)
def test_rejects_invalid_urls(url):
    with pytest.raises(InvalidRepositoryUrlError):
        parse_github_url(url)
