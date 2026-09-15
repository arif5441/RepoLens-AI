import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import get_session_factory  # noqa: E402


@pytest.fixture
def db_session():
    """A real session against the local MySQL database, rolled back after the test so nothing
    written during a test persists — no separate test database needed at this project's scale."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
