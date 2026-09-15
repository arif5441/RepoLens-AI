from fastapi import APIRouter, Depends

from app.api.dependencies import get_ollama_provider
from app.core.config import Settings, get_settings
from app.llm.ollama_provider import OllamaProvider
from app.schemas.llm import LLMChatRequest, LLMChatResponse, LLMModelsResponse
from app.services import llm_service

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


@router.post("/chat", response_model=LLMChatResponse)
def chat(
    request: LLMChatRequest,
    provider: OllamaProvider = Depends(get_ollama_provider),
    settings: Settings = Depends(get_settings),
) -> LLMChatResponse:
    return llm_service.chat(
        provider, settings, request.message, request.system_prompt, request.model
    )


@router.get("/models", response_model=LLMModelsResponse)
def models(provider: OllamaProvider = Depends(get_ollama_provider)) -> LLMModelsResponse:
    return llm_service.list_models(provider)
