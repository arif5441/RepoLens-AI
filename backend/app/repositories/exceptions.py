class RepositoryError(Exception):
    """Wraps any underlying database failure so callers never handle SQLAlchemy errors directly."""
