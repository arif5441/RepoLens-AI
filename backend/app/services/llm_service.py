import logging

from app.core.config import Settings
from app.llm.base import LLMProvider
from app.llm.exceptions import LLMProviderError
from app.llm.prompts import build_chat_messages
from app.schemas.llm import LLMChatResponse, LLMModelsResponse

logger = logging.getLogger(__name__)

PROVIDER_NAME = "ollama"


def chat(
    provider: LLMProvider,
    settings: Settings,
    message: str,
    system_prompt: str | None = None,
    model: str | None = None,
) -> LLMChatResponse:
    messages = build_chat_messages(message, system_prompt)
    resolved_model = model or settings.ollama_model

    try:
        result = provider.chat(messages, model=resolved_model, temperature=settings.llm_temperature)
    except LLMProviderError:
        logger.warning(
            "LLM chat failed | provider=%s model=%s message_length=%d",
            PROVIDER_NAME,
            resolved_model,
            len(message),
        )
        raise

    logger.info(
        "LLM chat succeeded | provider=%s model=%s duration_ms=%.0f message_length=%d",
        PROVIDER_NAME,
        result.model,
        result.duration_ms,
        len(message),
    )

    return LLMChatResponse(
        response=result.content,
        model=result.model,
        provider=PROVIDER_NAME,
        duration_ms=result.duration_ms,
    )


def list_models(provider: LLMProvider) -> LLMModelsResponse:
    return LLMModelsResponse(models=provider.list_models())
