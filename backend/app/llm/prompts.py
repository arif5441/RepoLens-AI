from app.llm.base import ChatMessage

SYSTEM_PROMPT = (
    "You are RepoLens, an AI assistant that helps developers understand software "
    "repositories. Answer clearly and concisely."
)


def build_chat_messages(user_message: str, system_prompt: str | None = None) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=system_prompt or SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_message),
    ]
