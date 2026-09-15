from fastapi import APIRouter, Depends

from app.api.dependencies import get_ollama_provider
from app.llm.ollama_provider import OllamaProvider
from app.schemas.health import HealthResponse
from app.services.health_service import get_health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(ollama_provider: OllamaProvider = Depends(get_ollama_provider)) -> HealthResponse:
    return get_health(ollama_provider)
