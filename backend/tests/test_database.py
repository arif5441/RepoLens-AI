from app.core.database import check_database_connection


def test_check_database_connection_returns_status_tuple():
    ok, error = check_database_connection()
    assert isinstance(ok, bool)
    if not ok:
        assert error is not None
