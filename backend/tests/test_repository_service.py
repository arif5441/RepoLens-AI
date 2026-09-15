import pytest

from app.embeddings.base import EmbeddingResult
from app.models.embedding import Embedding
from app.services import repository_service
from app.services.exceptions import RepositoryNotIndexedError


class FakeGitHubClient:
    def __init__(self, tree_entries, contents=None):
        self._tree_entries = tree_entries
        self._contents = contents or {}

    def get_default_branch(self, owner, repo):
        return "main"

    def get_tree(self, owner, repo, branch):
        return self._tree_entries, False

    def get_raw_content(self, owner, repo, branch, path):
        return self._contents.get(path)


class FakeEmbeddingProvider:
    def __init__(self, dimension=2, model="fake-model"):
        self._dimension = dimension
        self._model = model

    def is_available(self):
        return True, None

    def dimension(self):
        return self._dimension

    def embed(self, texts):
        # deterministic fake vectors: one-hot-ish based on text length parity
        vectors = [[1.0, 0.0] if len(t) % 2 == 0 else [0.0, 1.0] for t in texts]
        return EmbeddingResult(vectors=vectors, model=self._model, dimension=self._dimension, duration_ms=1.0)


class FakeEmbeddingRepository:
    def __init__(self):
        self.rows: list[Embedding] = []
        self._next_id = 1

    def save(self, content, model, dimension, vector, source_ref=None, extra_metadata=None,
              repository=None, file_path=None, start_line=None, end_line=None, symbol_name=None):
        row = Embedding(
            id=self._next_id, content=content, model=model, dimension=dimension, vector=vector,
            source_ref=source_ref, extra_metadata=extra_metadata, repository=repository,
            file_path=file_path, start_line=start_line, end_line=end_line, symbol_name=symbol_name,
        )
        self._next_id += 1
        self.rows.append(row)
        return row

    def list_by_repository(self, repository, model, limit=5000):
        return [r for r in self.rows if r.repository == repository and r.model == model][:limit]

    def list_indexed_repositories(self):
        repos = {}
        for row in self.rows:
            if row.repository:
                repos[row.repository] = repos.get(row.repository, 0) + 1
        return [(repo, count, "2026-01-01T00:00:00") for repo, count in repos.items()]

    def delete_by_repository(self, repository):
        before = len(self.rows)
        self.rows = [r for r in self.rows if r.repository != repository]
        return before - len(self.rows)


def _blob(path, size):
    return {"path": path, "type": "blob", "size": size}


def test_index_repository_chunks_and_stores_files():
    github_client = FakeGitHubClient(
        tree_entries=[_blob("main.py", 50)],
        contents={"main.py": "def foo():\n    return 1\n\ndef bar():\n    return 2\n"},
    )
    embedding_provider = FakeEmbeddingProvider()
    embedding_repository = FakeEmbeddingRepository()

    response = repository_service.index_repository(
        github_client, embedding_provider, embedding_repository,
        "https://github.com/octocat/demo",
        max_files=100, max_file_size_bytes=200_000, max_total_size_bytes=20_000_000,
        max_lines_per_chunk=80,
    )

    assert response.repository == "octocat/demo"
    assert response.files_included == 1
    assert response.chunks_created >= 2  # foo + bar
    assert response.chunks_stored == response.chunks_created
    assert len(embedding_repository.rows) == response.chunks_stored
    assert all(r.repository == "octocat/demo" for r in embedding_repository.rows)
    assert all(r.symbol_name in ("foo", "bar") for r in embedding_repository.rows)


def test_index_repository_with_no_included_files_stores_nothing():
    github_client = FakeGitHubClient(tree_entries=[_blob("image.png", 10)])
    embedding_provider = FakeEmbeddingProvider()
    embedding_repository = FakeEmbeddingRepository()

    response = repository_service.index_repository(
        github_client, embedding_provider, embedding_repository,
        "https://github.com/octocat/demo",
        max_files=100, max_file_size_bytes=200_000, max_total_size_bytes=20_000_000,
        max_lines_per_chunk=80,
    )

    assert response.chunks_created == 0
    assert response.chunks_stored == 0
    assert embedding_repository.rows == []


def test_reindexing_replaces_previous_chunks():
    github_client = FakeGitHubClient(
        tree_entries=[_blob("main.py", 20)], contents={"main.py": "def foo():\n    return 1\n"}
    )
    embedding_provider = FakeEmbeddingProvider()
    embedding_repository = FakeEmbeddingRepository()

    repository_service.index_repository(
        github_client, embedding_provider, embedding_repository,
        "https://github.com/octocat/demo", 100, 200_000, 20_000_000, 80,
    )
    first_count = len(embedding_repository.rows)

    repository_service.index_repository(
        github_client, embedding_provider, embedding_repository,
        "https://github.com/octocat/demo", 100, 200_000, 20_000_000, 80,
    )

    assert len(embedding_repository.rows) == first_count  # replaced, not doubled


def test_list_indexed_repositories_delegates_to_repository():
    embedding_repository = FakeEmbeddingRepository()
    embedding_repository.save(
        content="x", model="m1", dimension=2, vector=[1.0, 0.0],
        repository="octocat/demo", file_path="a.py",
    )

    response = repository_service.list_indexed_repositories(embedding_repository)

    assert response.repositories[0].repository == "octocat/demo"
    assert response.repositories[0].chunk_count == 1


def test_search_repository_ranks_by_similarity():
    embedding_repository = FakeEmbeddingRepository()
    embedding_repository.save(
        content="exact", model="fake-model", dimension=2, vector=[1.0, 0.0],
        repository="octocat/demo", file_path="a.py", start_line=1, end_line=2, symbol_name="foo",
    )
    embedding_repository.save(
        content="opposite", model="fake-model", dimension=2, vector=[0.0, 1.0],
        repository="octocat/demo", file_path="b.py", start_line=1, end_line=2, symbol_name="bar",
    )
    embedding_provider = FakeEmbeddingProvider()  # even-length query -> [1.0, 0.0]

    response = repository_service.search_repository(
        embedding_provider, embedding_repository, "octocat/demo", "abcd", limit=5
    )

    assert response.count == 2
    assert response.results[0].content == "exact"
    assert response.results[0].symbol_name == "foo"


def test_search_repository_raises_when_not_indexed():
    embedding_repository = FakeEmbeddingRepository()
    embedding_provider = FakeEmbeddingProvider()

    with pytest.raises(RepositoryNotIndexedError):
        repository_service.search_repository(
            embedding_provider, embedding_repository, "octocat/never-indexed", "query", limit=5
        )
