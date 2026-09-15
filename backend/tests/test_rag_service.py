from app.embeddings.base import EmbeddingResult
from app.llm.base import ChatResult
from app.models.embedding import Embedding
from app.services import rag_service


class FakeEmbeddingProvider:
    def is_available(self):
        return True, None

    def dimension(self):
        return 2

    def embed(self, texts):
        return EmbeddingResult(
            vectors=[[1.0, 0.0]] * len(texts), model="fake-model", dimension=2, duration_ms=1.0
        )


class FakeEmbeddingRepository:
    def __init__(self, rows=None):
        self.rows = rows or []

    def list_by_repository(self, repository, model, limit=5000):
        return [r for r in self.rows if r.repository == repository]


class FakeLLMProvider:
    def __init__(self, content="This is the answer, see [1]."):
        self._content = content
        self.last_messages = None

    def is_available(self):
        return True, None

    def list_models(self):
        return []

    def chat(self, messages, model, temperature):
        self.last_messages = messages
        return ChatResult(content=self._content, model=model, duration_ms=5.0)


def _row(content, repository="octocat/demo", path="a.py", similarity_vector=None):
    return Embedding(
        id=1, content=content, model="fake-model", dimension=2,
        vector=similarity_vector or [1.0, 0.0], repository=repository, file_path=path,
        start_line=1, end_line=5, symbol_name="foo",
    )


def test_ask_returns_grounded_answer_with_citations():
    embedding_repository = FakeEmbeddingRepository(rows=[_row("def foo(): pass")])
    llm_provider = FakeLLMProvider()

    response = rag_service.ask(
        FakeEmbeddingProvider(), embedding_repository, llm_provider,
        "octocat/demo", "what does foo do?", top_k=5, min_similarity=0.2,
        max_context_chars=6000, llm_model="phi3:mini", temperature=0.3,
    )

    assert response.grounded is True
    assert response.answer == "This is the answer, see [1]."
    assert len(response.citations) == 1
    assert response.citations[0].file_path == "a.py"


def test_ask_builds_prompt_containing_retrieved_content():
    embedding_repository = FakeEmbeddingRepository(rows=[_row("def foo(): return 42")])
    llm_provider = FakeLLMProvider()

    rag_service.ask(
        FakeEmbeddingProvider(), embedding_repository, llm_provider,
        "octocat/demo", "what does foo return?", top_k=5, min_similarity=0.2,
        max_context_chars=6000, llm_model="phi3:mini", temperature=0.3,
    )

    user_message = llm_provider.last_messages[1].content
    assert "def foo(): return 42" in user_message
    assert "what does foo return?" in user_message


def test_ask_returns_insufficient_evidence_when_nothing_relevant():
    embedding_repository = FakeEmbeddingRepository(rows=[])  # nothing indexed at all -> raises
    llm_provider = FakeLLMProvider()

    # index a repo with only a low-similarity row via a repository object whose vector never
    # matches well: use a fake embedding provider producing a query vector orthogonal to stored.
    class OrthogonalEmbeddingProvider(FakeEmbeddingProvider):
        def embed(self, texts):
            return EmbeddingResult(
                vectors=[[0.0, 1.0]] * len(texts), model="fake-model", dimension=2, duration_ms=1.0
            )

    repo_with_row = FakeEmbeddingRepository(rows=[_row("unrelated content")])

    response = rag_service.ask(
        OrthogonalEmbeddingProvider(), repo_with_row, llm_provider,
        "octocat/demo", "irrelevant question", top_k=5, min_similarity=0.5,
        max_context_chars=6000, llm_model="phi3:mini", temperature=0.3,
    )

    assert response.grounded is False
    assert response.citations == []
    assert "could not find enough evidence" in response.answer.lower()
    assert llm_provider.last_messages is None  # LLM was never called
