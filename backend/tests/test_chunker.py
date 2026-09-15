from app.chunking.chunker import chunk_source_file
from app.ingestion.models import SourceFile


def _file(content: str, language: str = "python", path: str = "main.py") -> SourceFile:
    return SourceFile(
        path=path, language=language, content=content, size_bytes=len(content),
        repository="octocat/demo", ref="main",
    )


def test_empty_file_produces_no_chunks():
    assert chunk_source_file(_file("")) == []


def test_python_functions_become_separate_chunks():
    content = "\n".join(
        [
            "import os",
            "",
            "def foo():",
            "    return 1",
            "",
            "def bar():",
            "    return 2",
        ]
    )
    chunks = chunk_source_file(_file(content))

    symbols = [c.symbol_name for c in chunks]
    assert "foo" in symbols
    assert "bar" in symbols
    # preamble (import) before the first def should be its own chunk with no symbol
    assert None in symbols


def test_chunks_have_correct_line_ranges():
    content = "\n".join(["def foo():", "    return 1", "", "def bar():", "    return 2"])
    chunks = chunk_source_file(_file(content))

    foo_chunk = next(c for c in chunks if c.symbol_name == "foo")
    bar_chunk = next(c for c in chunks if c.symbol_name == "bar")

    assert foo_chunk.start_line == 1
    assert foo_chunk.end_line == 2
    assert bar_chunk.start_line == 4
    assert bar_chunk.end_line == 5


def test_python_class_detected_as_symbol():
    content = "\n".join(["class Foo:", "    def method(self):", "        pass"])
    chunks = chunk_source_file(_file(content))

    assert any(c.symbol_name == "Foo" for c in chunks)


def test_chunk_index_is_sequential():
    content = "\n".join(["def a():", "    pass", "def b():", "    pass", "def c():", "    pass"])
    chunks = chunk_source_file(_file(content))

    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_large_function_split_into_sub_chunks_under_max_lines():
    body = "\n".join(f"    x{i} = {i}" for i in range(200))
    content = f"def big():\n{body}"

    chunks = chunk_source_file(_file(content), max_lines=50)

    assert len(chunks) > 1
    assert all(c.end_line - c.start_line + 1 <= 50 for c in chunks)
    assert all(c.symbol_name == "big" for c in chunks)


def test_javascript_function_and_class_detected():
    content = "\n".join(
        ["function greet() {", "  return 'hi';", "}", "", "class Widget {", "  render() {}", "}"]
    )
    chunks = chunk_source_file(_file(content, language="javascript", path="app.js"))

    symbols = {c.symbol_name for c in chunks}
    assert "greet" in symbols
    assert "Widget" in symbols


def test_go_function_with_receiver_detected():
    content = "\n".join(["func (s *Server) Start() error {", "\treturn nil", "}"])
    chunks = chunk_source_file(_file(content, language="go", path="main.go"))

    assert any(c.symbol_name == "Start" for c in chunks)


def test_unsupported_language_falls_back_to_line_chunking():
    content = "\n".join(f"line {i}" for i in range(150))
    chunks = chunk_source_file(_file(content, language="markdown", path="README.md"), max_lines=50)

    assert len(chunks) == 3
    assert all(c.symbol_name is None for c in chunks)
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 50
    assert chunks[1].start_line == 51


def test_file_with_no_detected_boundaries_falls_back_to_line_chunking():
    content = "\n".join(["x = 1", "y = 2", "z = x + y"])
    chunks = chunk_source_file(_file(content))

    assert len(chunks) == 1
    assert chunks[0].symbol_name is None
    assert chunks[0].content == content


def test_trailing_blank_lines_excluded_from_chunk():
    content = "def foo():\n    return 1\n\n\n"
    chunks = chunk_source_file(_file(content))

    assert chunks[0].end_line == 2
