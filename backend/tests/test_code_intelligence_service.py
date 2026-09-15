import pytest

from app.llm.base import ChatResult
from app.models.embedding import Embedding
from app.services import code_intelligence_service
from app.services.exceptions import FileNotIndexedError


class FakeLLMProvider:
    def __init__(self):
        self.last_messages = None

    def is_available(self):
        return True, None

    def list_models(self):
        return []

    def chat(self, messages, model, temperature):
        self.last_messages = messages
        return ChatResult(content="This file defines a Foo class.", model=model, duration_ms=3.0)


class FakeEmbeddingRepository:
    def __init__(self, rows=None):
        self.rows = rows or []

    def list_by_repository_and_path(self, repository, model, file_path):
        return [
            r for r in self.rows
            if r.repository == repository and r.file_path == file_path
        ]


def _row(content, start, end, path="main.py"):
    return Embedding(
        id=1, content=content, model="fake-model", dimension=2, vector=[1.0, 0.0],
        repository="octocat/demo", file_path=path, start_line=start, end_line=end,
    )


def test_explain_file_returns_llm_explanation():
    repo = FakeEmbeddingRepository(rows=[_row("class Foo: pass", 1, 1)])
    llm = FakeLLMProvider()

    response = code_intelligence_service.explain_file(
        repo, llm, "octocat/demo", "main.py",
        embedding_model="fake-model", llm_model="phi3:mini", temperature=0.3,
    )

    assert response.explanation == "This file defines a Foo class."
    assert response.chunk_count == 1
    assert response.repository == "octocat/demo"
    assert response.path == "main.py"


def test_explain_file_includes_all_chunks_in_prompt():
    repo = FakeEmbeddingRepository(
        rows=[_row("class Foo: pass", 1, 1), _row("def bar(): pass", 3, 3)]
    )
    llm = FakeLLMProvider()

    code_intelligence_service.explain_file(
        repo, llm, "octocat/demo", "main.py",
        embedding_model="fake-model", llm_model="phi3:mini", temperature=0.3,
    )

    prompt_content = llm.last_messages[1].content
    assert "class Foo: pass" in prompt_content
    assert "def bar(): pass" in prompt_content


def test_explain_file_raises_when_file_not_indexed():
    repo = FakeEmbeddingRepository(rows=[])
    llm = FakeLLMProvider()

    with pytest.raises(FileNotIndexedError):
        code_intelligence_service.explain_file(
            repo, llm, "octocat/demo", "missing.py",
            embedding_model="fake-model", llm_model="phi3:mini", temperature=0.3,
        )
