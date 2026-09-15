import re

from app.ingestion.exceptions import InvalidRepositoryUrlError

# https://github.com/owner/repo, with optional trailing slash, .git suffix, or www.
_GITHUB_URL_RE = re.compile(
    r"^https?://(www\.)?github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(\.git)?/?$"
)


def parse_github_url(url: str) -> tuple[str, str]:
    """Extracts (owner, repo) from a public GitHub repository URL. Raises
    InvalidRepositoryUrlError if the URL isn't a recognizable GitHub repo URL."""
    match = _GITHUB_URL_RE.match(url.strip())
    if not match:
        raise InvalidRepositoryUrlError(
            "expected a URL like https://github.com/owner/repository"
        )
    return match.group("owner"), match.group("repo")
