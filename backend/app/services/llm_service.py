import logging

from app.core.config import Settings
from app.llm.base import LLMProvider
from app.llm.exceptions import LLMProviderError
from app.llm.prompts import build_chat_messages
from app.schemas.llm import LLMChatResponse

logger = logging.getLogger(__name__)

PROVIDER_NAME = "ollama"


def chat(provider: LLMProvider, settings: Settings, message: str) -> LLMChatResponse:
    messages = build_chat_messages(message)

    try:
        result = provider.chat(messages, model=settings.ollama_model, temperature=settings.llm_temperature)
    except LLMProviderError:
        logger.warning(
            "LLM chat failed | provider=%s model=%s message_length=%d",
            PROVIDER_NAME,
            settings.ollama_model,
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
