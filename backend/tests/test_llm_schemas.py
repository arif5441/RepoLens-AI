import pytest
from pydantic import ValidationError

from app.schemas.llm import LLMChatRequest


def test_valid_message_accepted():
    request = LLMChatRequest(message="Explain dependency injection.")
    assert request.message == "Explain dependency injection."


def test_empty_message_rejected():
    with pytest.raises(ValidationError):
        LLMChatRequest(message="")


def test_whitespace_only_message_not_rejected_by_schema():
    # min_length checks character count, not blankness — this documents that
    # the schema alone won't catch "   ". Acceptable at this phase: the model
    # just returns a low-value response rather than the app crashing.
    request = LLMChatRequest(message=" ")
    assert request.message == " "
