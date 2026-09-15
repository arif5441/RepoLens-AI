from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env lives at the project root (one level above backend/), not inside backend/.
_PROJECT_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT_ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "development"
    app_log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:4200"

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "repolens"
    mysql_user: str = "repolens"
    mysql_password: str = ""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "phi3:mini"
    ollama_chat_timeout_seconds: float = 60.0
    llm_temperature: float = 0.3

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    embedding_normalize: bool = True

    github_token: str | None = None
    github_api_base_url: str = "https://api.github.com"
    github_raw_base_url: str = "https://raw.githubusercontent.com"
    ingestion_http_timeout_seconds: float = 15.0
    ingestion_max_files: int = 300
    ingestion_max_file_size_bytes: int = 200_000
    ingestion_max_total_size_bytes: int = 20_000_000
    chunk_max_lines: int = 80

    rag_top_k: int = 5
    rag_min_similarity: float = 0.2
    rag_max_context_chars: int = 6000

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def mysql_url(self) -> str:
        user = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        return f"mysql+pymysql://{user}:{password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
