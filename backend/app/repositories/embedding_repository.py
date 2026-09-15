from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.embedding import Embedding
from app.repositories.exceptions import RepositoryError


class EmbeddingRepository:
    """Data access for stored embedding vectors. Callers never touch SQLAlchemy directly."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(
        self,
        content: str,
        model: str,
        dimension: int,
        vector: list[float],
        source_ref: str | None = None,
        extra_metadata: dict | None = None,
        repository: str | None = None,
        file_path: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        symbol_name: str | None = None,
    ) -> Embedding:
        try:
            row = Embedding(
                content=content,
                model=model,
                dimension=dimension,
                vector=vector,
                source_ref=source_ref,
                extra_metadata=extra_metadata,
                repository=repository,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                symbol_name=symbol_name,
            )
            self._session.add(row)
            self._session.flush()  # populate row.id without committing the outer transaction
            return row
        except SQLAlchemyError as exc:
            raise RepositoryError(f"could not save embedding: {exc}") from exc

    def get(self, embedding_id: int) -> Embedding | None:
        try:
            return self._session.get(Embedding, embedding_id)
        except SQLAlchemyError as exc:
            raise RepositoryError(f"could not fetch embedding {embedding_id}: {exc}") from exc

    def delete(self, embedding_id: int) -> bool:
        try:
            row = self._session.get(Embedding, embedding_id)
            if row is None:
                return False
            self._session.delete(row)
            self._session.flush()
            return True
        except SQLAlchemyError as exc:
            raise RepositoryError(f"could not delete embedding {embedding_id}: {exc}") from exc

    def list_by_model(self, model: str, limit: int = 1000) -> list[Embedding]:
        """Candidates for a brute-force similarity search — always scoped to one model,
        since vectors from different models aren't comparable (different dimension/meaning)."""
        try:
            return (
                self._session.query(Embedding)
                .filter(Embedding.model == model)
                .order_by(Embedding.id.desc())
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:
            raise RepositoryError(f"could not list embeddings for model '{model}': {exc}") from exc

    def list_by_repository(self, repository: str, model: str, limit: int = 5000) -> list[Embedding]:
        """Candidates for a repository-scoped similarity search (RAG retrieval)."""
        try:
            return (
                self._session.query(Embedding)
                .filter(Embedding.repository == repository, Embedding.model == model)
                .order_by(Embedding.id.asc())
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:
            raise RepositoryError(
                f"could not list embeddings for repository '{repository}': {exc}"
            ) from exc

    def list_by_repository_and_path(self, repository: str, model: str, file_path: str) -> list[Embedding]:
        """All chunks for one file in one repository — used by code explanation (Phase 8)."""
        try:
            return (
                self._session.query(Embedding)
                .filter(
                    Embedding.repository == repository,
                    Embedding.model == model,
                    Embedding.file_path == file_path,
                )
                .order_by(Embedding.start_line.asc())
                .all()
            )
        except SQLAlchemyError as exc:
            raise RepositoryError(
                f"could not list embeddings for {repository}:{file_path}: {exc}"
            ) from exc

    def list_indexed_repositories(self) -> list[tuple[str, int, str]]:
        """Distinct repositories with a chunk count and last-indexed timestamp, for repository
        management UI. Returns (repository, chunk_count, last_indexed_at_iso)."""
        try:
            rows = (
                self._session.query(
                    Embedding.repository,
                    func.count(Embedding.id),
                    func.max(Embedding.updated_at),
                )
                .filter(Embedding.repository.is_not(None))
                .group_by(Embedding.repository)
                .order_by(func.max(Embedding.updated_at).desc())
                .all()
            )
            return [(repo, count, updated_at.isoformat()) for repo, count, updated_at in rows]
        except SQLAlchemyError as exc:
            raise RepositoryError(f"could not list indexed repositories: {exc}") from exc

    def delete_by_repository(self, repository: str) -> int:
        """Removes every stored chunk for a repository (used before re-indexing)."""
        try:
            deleted = (
                self._session.query(Embedding).filter(Embedding.repository == repository).delete()
            )
            self._session.flush()
            return deleted
        except SQLAlchemyError as exc:
            raise RepositoryError(f"could not delete embeddings for '{repository}': {exc}") from exc
