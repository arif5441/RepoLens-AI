"""Real end-to-end test against a locally running Ollama. Skips automatically if unavailable."""

import httpx
import pytest

from app.core.config import get_settings

settings = get_settings()


def _ollama_is_up() -> bool:
    try:
        httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=2.0).raise_for_status()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _ollama_is_up(), reason="Ollama is not running locally")
def test_real_chat_round_trip():
    from app.llm.ollama_provider import OllamaProvider
    from app.llm.prompts import build_chat_messages

    provider = OllamaProvider(base_url=settings.ollama_base_url)
    messages = build_chat_messages("Reply with the single word: pong")

    result = provider.chat(messages, model=settings.ollama_model, temperature=0.0)

    assert result.content.strip() != ""
    assert result.duration_ms > 0
