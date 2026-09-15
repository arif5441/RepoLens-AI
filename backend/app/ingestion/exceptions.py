class IngestionError(Exception):
    """Base for all repository ingestion failures."""


class InvalidRepositoryUrlError(IngestionError):
    """The given URL isn't a recognizable public GitHub repository URL."""


class RepositoryNotFoundError(IngestionError):
    """The repository doesn't exist, or is private/inaccessible without auth.

    GitHub's unauthenticated API returns 404 for both cases — there's no way to tell them
    apart without a token, so the message stays deliberately generic.
    """


class GitHubRateLimitedError(IngestionError):
    """GitHub's API rate limit was hit (60 requests/hour unauthenticated)."""


class GitHubRequestError(IngestionError):
    """An unexpected error occurred talking to GitHub."""
