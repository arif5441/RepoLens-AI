class RepositoryNotIndexedError(Exception):
    """Raised when searching/asking against a repository that has no stored chunks yet."""

    def __init__(self, repository: str) -> None:
        self.repository = repository
        super().__init__(f"'{repository}' has not been indexed yet — index it first")


class FileNotIndexedError(Exception):
    """Raised when asking to explain a file that has no stored chunks for that repository."""

    def __init__(self, repository: str, path: str) -> None:
        self.repository = repository
        self.path = path
        super().__init__(f"'{path}' in '{repository}' has no indexed chunks")
