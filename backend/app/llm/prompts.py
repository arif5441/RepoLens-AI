from app.llm.base import ChatMessage

SYSTEM_PROMPT = (
    "You are RepoLens, an AI assistant that helps developers understand software "
    "repositories. Answer clearly and concisely."
)


def build_chat_messages(user_message: str) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_message),
    ]
