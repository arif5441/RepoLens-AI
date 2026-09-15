"""Repository tests against the real local MySQL database. Each test runs inside a session that
gets rolled back afterwards (see conftest.db_session), so nothing written here persists."""

from app.repositories.embedding_repository import EmbeddingRepository


def test_save_returns_row_with_id(db_session):
    repo = EmbeddingRepository(db_session)

    row = repo.save(content="hello world", model="test-model", dimension=3, vector=[0.1, 0.2, 0.3])

    assert row.id is not None
    assert row.content == "hello world"
    assert row.model == "test-model"
    assert row.dimension == 3
    assert row.vector == [0.1, 0.2, 0.3]
    assert row.created_at is not None


def test_save_with_source_ref_and_metadata(db_session):
    repo = EmbeddingRepository(db_session)

    row = repo.save(
        content="hello",
        model="test-model",
        dimension=2,
        vector=[0.1, 0.2],
        source_ref="chunk:42",
        extra_metadata={"origin": "unit-test"},
    )

    assert row.source_ref == "chunk:42"
    assert row.extra_metadata == {"origin": "unit-test"}


def test_get_returns_saved_row(db_session):
    repo = EmbeddingRepository(db_session)
    saved = repo.save(content="findme", model="test-model", dimension=2, vector=[1.0, 0.0])

    fetched = repo.get(saved.id)

    assert fetched is not None
    assert fetched.content == "findme"


def test_get_returns_none_for_missing_id(db_session):
    repo = EmbeddingRepository(db_session)

    assert repo.get(999_999_999) is None


def test_delete_removes_row(db_session):
    repo = EmbeddingRepository(db_session)
    saved = repo.save(content="temporary", model="test-model", dimension=2, vector=[1.0, 0.0])

    deleted = repo.delete(saved.id)

    assert deleted is True
    assert repo.get(saved.id) is None


def test_delete_returns_false_for_missing_id(db_session):
    repo = EmbeddingRepository(db_session)

    assert repo.delete(999_999_999) is False


def test_list_by_model_only_returns_matching_model(db_session):
    repo = EmbeddingRepository(db_session)
    repo.save(content="a", model="model-x", dimension=2, vector=[1.0, 0.0])
    repo.save(content="b", model="model-y", dimension=2, vector=[0.0, 1.0])

    results = repo.list_by_model("model-x")

    assert all(row.model == "model-x" for row in results)
    assert any(row.content == "a" for row in results)
    assert not any(row.content == "b" for row in results)


def test_save_with_chunk_fields(db_session):
    repo = EmbeddingRepository(db_session)

    row = repo.save(
        content="def foo(): pass",
        model="test-model",
        dimension=2,
        vector=[1.0, 0.0],
        repository="octocat/demo",
        file_path="app/main.py",
        start_line=10,
        end_line=12,
        symbol_name="foo",
    )

    assert row.repository == "octocat/demo"
    assert row.file_path == "app/main.py"
    assert row.start_line == 10
    assert row.end_line == 12
    assert row.symbol_name == "foo"


def test_list_by_repository_scopes_to_repository_and_model(db_session):
    repo = EmbeddingRepository(db_session)
    repo.save(
        content="a", model="m1", dimension=2, vector=[1.0, 0.0],
        repository="octocat/demo", file_path="a.py",
    )
    repo.save(
        content="b", model="m1", dimension=2, vector=[0.0, 1.0],
        repository="octocat/other", file_path="b.py",
    )

    results = repo.list_by_repository("octocat/demo", "m1")

    assert all(row.repository == "octocat/demo" for row in results)
    assert any(row.content == "a" for row in results)
    assert not any(row.content == "b" for row in results)


def test_list_by_repository_and_path_orders_by_start_line(db_session):
    repo = EmbeddingRepository(db_session)
    repo.save(
        content="second", model="m1", dimension=2, vector=[1.0, 0.0],
        repository="octocat/demo", file_path="main.py", start_line=20, end_line=25,
    )
    repo.save(
        content="first", model="m1", dimension=2, vector=[1.0, 0.0],
        repository="octocat/demo", file_path="main.py", start_line=1, end_line=10,
    )

    results = repo.list_by_repository_and_path("octocat/demo", "m1", "main.py")

    assert [row.content for row in results] == ["first", "second"]


def test_list_indexed_repositories_returns_counts(db_session):
    repo = EmbeddingRepository(db_session)
    repo.save(
        content="a", model="m1", dimension=2, vector=[1.0, 0.0],
        repository="octocat/countme", file_path="a.py",
    )
    repo.save(
        content="b", model="m1", dimension=2, vector=[1.0, 0.0],
        repository="octocat/countme", file_path="b.py",
    )

    rows = repo.list_indexed_repositories()

    entry = next(r for r in rows if r[0] == "octocat/countme")
    assert entry[1] == 2


def test_delete_by_repository_removes_all_matching_rows(db_session):
    repo = EmbeddingRepository(db_session)
    repo.save(
        content="a", model="m1", dimension=2, vector=[1.0, 0.0],
        repository="octocat/deleteme", file_path="a.py",
    )
    repo.save(
        content="b", model="m1", dimension=2, vector=[1.0, 0.0],
        repository="octocat/deleteme", file_path="b.py",
    )

    deleted_count = repo.delete_by_repository("octocat/deleteme")

    assert deleted_count == 2
    assert repo.list_by_repository("octocat/deleteme", "m1") == []
