from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.embeddings.local_provider import LocalEmbeddingProvider
from app.ingestion.github_client import GitHubClient
from app.llm.ollama_provider import OllamaProvider
from app.repositories.embedding_repository import EmbeddingRepository


def get_ollama_provider(settings: Settings = Depends(get_settings)) -> OllamaProvider:
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        chat_timeout_seconds=settings.ollama_chat_timeout_seconds,
    )


def get_embedding_provider(settings: Settings = Depends(get_settings)) -> LocalEmbeddingProvider:
    return LocalEmbeddingProvider(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        normalize=settings.embedding_normalize,
    )


def get_embedding_repository(session: Session = Depends(get_db)) -> EmbeddingRepository:
    return EmbeddingRepository(session)


def get_github_client(settings: Settings = Depends(get_settings)) -> GitHubClient:
    return GitHubClient(
        api_base_url=settings.github_api_base_url,
        raw_base_url=settings.github_raw_base_url,
        token=settings.github_token,
        timeout_seconds=settings.ingestion_http_timeout_seconds,
    )
