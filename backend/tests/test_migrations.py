"""Verifies the embeddings table Alembic created matches what the ORM model expects."""

from sqlalchemy import inspect

from app.core.database import get_engine


def test_embeddings_table_exists_with_expected_columns():
    inspector = inspect(get_engine())

    assert "embeddings" in inspector.get_table_names()

    columns = {col["name"] for col in inspector.get_columns("embeddings")}
    assert columns == {
        "id",
        "content",
        "source_ref",
        "model",
        "dimension",
        "vector",
        "extra_metadata",
        "created_at",
        "updated_at",
        "repository",
        "file_path",
        "start_line",
        "end_line",
        "symbol_name",
    }


def test_embeddings_table_has_model_dimension_index():
    inspector = inspect(get_engine())

    index_columns = [
        set(index["column_names"])
        for index in inspector.get_indexes("embeddings")
        if index["name"] == "ix_embeddings_model_dimension"
    ]

    assert {"model", "dimension"} in index_columns


def test_embeddings_table_has_repository_model_index():
    inspector = inspect(get_engine())

    index_columns = [
        set(index["column_names"])
        for index in inspector.get_indexes("embeddings")
        if index["name"] == "ix_embeddings_repository_model"
    ]

    assert {"repository", "model"} in index_columns
