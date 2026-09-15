from app.core.config import get_settings


def test_settings_load_from_env():
    settings = get_settings()
    assert settings.mysql_database
    assert settings.api_port > 0


def test_mysql_url_encodes_special_characters():
    settings = get_settings()
    settings = settings.model_copy(update={"mysql_user": "a@b", "mysql_password": "p@ss"})
    url = settings.mysql_url
    assert "a%40b" in url
    assert "p%40ss" in url
