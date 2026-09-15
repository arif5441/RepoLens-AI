# RepoLens AI — Architecture Overview

Status: **Phase 0 (foundation)**. This document distinguishes implemented architecture from planned architecture throughout. Nothing described here as "implemented" exists until `FEATURE.md` marks it `[x]`.

---

## 1. Product Overview

RepoLens AI indexes a public GitHub repository and lets a developer ask natural-language questions about its source code. Unlike a generic LLM chat wrapper, every answer is grounded in retrieved source code chunks and cites file/function/line-level evidence. If the system cannot find sufficient evidence, it says so instead of guessing.

**Problem it solves**: understanding an unfamiliar codebase is slow. Grep and manual reading don't surface cross-file relationships or intent. Generic LLM chat (paste-and-ask) hallucinates APIs and can't cite real locations. RepoLens combines semantic code retrieval with a local LLM to answer questions with verifiable evidence.

---

## 2. High-Level Architecture (Planned)

```text
Angular (Fiori-style UI)
   ↓  HTTP/REST
FastAPI (API layer)
   ↓
Application Services (domain logic)
   ↓
RAG Pipeline (retrieval → context → prompt → LLM)
   ↓
Retrieval Service  ←→  MySQL (app data + embeddings)
   ↓
LLM Provider Abstraction → Ollama (local LLM)
```

Nothing in this stack is implemented yet beyond the directory scaffold. Phase 0 builds the FastAPI/Angular/MySQL skeleton; later phases fill in ingestion, embeddings, retrieval, and RAG.

---

## 3. Complete Data Flow (Planned)

### Ingestion (offline / on-demand, triggered per repository)

```text
GitHub Repository URL
        ↓
Repository Ingestion (clone, depth-limited, no hook execution)
        ↓
File Discovery (respect .gitignore, size/binary filters)
        ↓
Code Parsing (per-language)
        ↓
Code Chunking (function/class-aware, not fixed-size)
        ↓
Metadata Extraction (file path, language, class, function, start/end line)
        ↓
Embedding Generation (local embedding model)
        ↓
MySQL Storage (chunk text + metadata + embedding vector)
```

### Query (online, per user question)

```text
User Question
        ↓
Question Embedding (same embedding model as ingestion)
        ↓
Retrieval (similarity search + metadata filtering, in MySQL)
        ↓
Relevant Code Chunks (ranked)
        ↓
Context Construction (assemble chunks + citations into prompt context)
        ↓
Prompt Construction (question + context + grounding instructions)
        ↓
Local LLM (Ollama, via LLMProvider)
        ↓
Grounded Answer
        ↓
Source Citations (file, function, start–end line, chunk ID)
```

---

## 4. Major Components (Planned)

- **Angular frontend** — Fiori-style enterprise UI: repository management, indexing status, chat interface, source viewer, architecture/documentation views, evaluation view. Talks to FastAPI over REST.
- **FastAPI API layer** (`backend/app/api`) — thin HTTP layer: request validation (Pydantic schemas), calls into services, typed responses. No business logic here.
- **Application/domain services** (`backend/app/services`) — orchestrate use cases (e.g. "index a repository", "answer a question"), calling ingestion/embeddings/retrieval/rag/llm modules and repositories.
- **Repository ingestion** (`backend/app/ingestion`) — clone/download a repo safely, walk files, filter, detect language.
- **Code parser** (`backend/app/ingestion`) — language-aware parsing to locate function/class boundaries for chunking.
- **Chunker** (`backend/app/ingestion` or dedicated module — TBD at Phase 4) — splits parsed source into code-aware chunks with metadata.
- **Embedding service** (`backend/app/embeddings`) — wraps `EmbeddingProvider` to turn text (code chunks, questions) into vectors.
- **Retrieval service** (`backend/app/retrieval`) — similarity search + metadata filtering + ranking over stored embeddings.
- **RAG orchestration** (`backend/app/rag`) — ties retrieval + context construction + prompt construction + LLM call + citation assembly into the grounded-answer pipeline.
- **LLM provider abstraction** (`backend/app/llm`) — `LLMProvider` interface, `OllamaLLMProvider` implementation. Isolates the rest of the app from the specific LLM backend.
- **Ollama** — local LLM runtime, called only through `LLMProvider`.
- **MySQL** — single datastore for application data (projects, repos, files, conversations) and embedding storage (see §5). No separate vector DB.
- **Evaluation system** (`evaluation/`, Phase 8) — measures retrieval and answer quality against a curated dataset.

---

## 5. Database Architecture (Planned — not yet implemented)

```text
projects
repositories
repository_files
code_chunks
conversations
messages
evaluation_cases
evaluation_results
```

- **projects** — a user-facing grouping/workspace concept (e.g. "my exploration of repo X"). Exists so conversations and indexed repos have a container.
- **repositories** — one row per indexed GitHub repo: URL, default branch, last indexed commit SHA, indexing status.
- **repository_files** — discovered files per repository: path, language, size, inclusion/exclusion reason.
- **code_chunks** — the retrieval unit: chunk text, file reference, class/function name, start/end line, embedding vector, chunk ID. This is what retrieval queries against.
- **conversations** — a question/answer session scoped to a repository.
- **messages** — individual question/answer turns within a conversation, including which chunk IDs were cited.
- **evaluation_cases** — curated (question, expected evidence) pairs used to measure system quality.
- **evaluation_results** — recorded outcomes of running evaluation_cases against the pipeline, over time (for regression tracking).

No migrations or ORM models exist yet. Migration tooling choice (e.g. Alembic) will be documented here when Phase 0's MySQL connection work lands.

### Vector storage in MySQL (why no dedicated vector DB)

MySQL does not have native ANN (approximate nearest neighbor) indexing the way Qdrant/Pinecone do. For a portfolio-scale project (single-user, moderate repo sizes), brute-force cosine similarity over stored embedding vectors — computed in Python or via SQL — is fast enough and avoids adding infrastructure. This is a deliberate scale tradeoff, documented so it isn't mistaken for an oversight. Revisit only if retrieval latency becomes a real bottleneck (see §7 Future Architecture).

---

## 6. AI Architecture — Concepts (for an engineer new to AI)

Explanations are scoped to how each concept is actually used in RepoLens, not general ML theory.

- **LLM (Large Language Model)** — a model that predicts text continuations. In RepoLens, the LLM's only job is to turn (question + retrieved code) into a readable, grounded answer. It does not decide what code is relevant — retrieval does that.
- **Tokens** — the units LLMs process text in (roughly word-pieces). Matters here because: (1) local models have context-length limits, so context construction must fit retrieved chunks within a token budget, (2) prompt size affects local inference speed.
- **Embeddings** — a numeric vector representation of text such that semantically similar text has vectors close together. RepoLens embeds every code chunk once at ingestion time, and embeds each user question at query time, using the *same* embedding model so they're comparable.
- **Vectors / semantic similarity** — comparing two embeddings (typically via cosine similarity) gives a similarity score. High similarity between a question's embedding and a code chunk's embedding suggests that chunk is relevant to the question — even if it doesn't share exact keywords.
- **Retrieval** — the process of finding the top-N most relevant code chunks for a question, via embedding similarity (and metadata filters like language/file). This is the retrieval half of "RAG."
- **RAG (Retrieval-Augmented Generation)** — instead of asking the LLM to answer from its own training knowledge (which doesn't include this specific repo and would hallucinate), retrieve real chunks from *this* repo first and hand them to the LLM as context. The LLM's answer is then grounded in real, retrieved text.
- **Hallucination** — an LLM generating plausible-sounding but false content (e.g. inventing a function that doesn't exist). RAG reduces this by grounding answers in retrieved evidence; explicit prompt instructions and citation requirements reduce it further.
- **Grounding** — the practice of constraining/checking LLM output against retrieved source material so claims are traceable to real content, not the model's own invention.
- **Citations** — RepoLens attaches file/function/line evidence to every claim so a developer can verify the answer against real code, rather than trusting the LLM blindly.
- **Evaluation** — since LLM output isn't deterministic and can't be checked with exact string equality, quality is measured with a curated dataset of questions with known correct evidence, checking whether retrieval found the right chunks and whether the answer's citations match.

---

## 7. Design Decisions

| Decision | Reasoning |
|---|---|
| **Local LLM (not a paid API)** | Free-first requirement — the project must be usable with zero recurring cost and no vendor API key. |
| **Ollama** | Simplest way to run local LLMs with a stable HTTP API, good model selection, no custom inference code needed. |
| **MySQL (not Postgres/a vector DB)** | Engineer already has strong MySQL/relational experience; avoids adding infrastructure (Docker, Qdrant, etc.) before it's justified; brute-force similarity is adequate at this scale (see §5). |
| **LangChain** | Provides tested primitives for prompt templates, document loaders, and LLM/embedding provider interfaces so we're not reinventing plumbing — used as glue, not as the source of the app's core logic (retrieval ranking, chunking, citation assembly stay custom and explicit). |
| **Angular (not React/Vue)** | Matches the developer's existing production frontend experience; strong typing and structure fit an enterprise-tool UI. |
| **Code-aware chunking (not fixed-size text splitting)** | Splitting code at arbitrary character counts breaks functions/classes mid-body, destroying retrieval quality and making citations meaningless. Chunking at function/class boundaries keeps each chunk semantically coherent and citable. |
| **Source citations required** | Without them, answers are unverifiable — the core value proposition (trustworthy code Q&A) depends on being able to check every claim against real code. |
| **Evaluation system (Phase 8)** | LLM/retrieval quality is not obvious from reading code or a few manual tests; a measurable evaluation harness is what turns "seems to work" into a defensible engineering claim — important for a portfolio project. |
| **No Docker in Phase 0–N** | Adds operational complexity before there's a multi-service deployment need; local Python/Node/MySQL/Ollama setup is sufficient for a single-developer local tool. Revisit if/when packaging for others to self-host becomes a goal. |

---

## 8. Future Architecture (explicitly not implemented)

Distinguishing these from the above so nothing here is mistaken for current behavior:

- Hybrid retrieval (keyword + semantic) — only if evaluation shows pure semantic retrieval misses obvious keyword matches (e.g. exact function names).
- Dedicated vector database — only if MySQL brute-force similarity becomes a measured bottleneck at realistic repo sizes.
- Dockerized deployment — only if the project moves toward being self-hosted by others.
- Optional paid LLM/embedding provider — only behind the existing `LLMProvider`/`EmbeddingProvider` abstractions, opt-in, default behavior unaffected.
- Multi-repository cross-referencing, reranking models, authentication/multi-user support — not scoped for the current phases; would need explicit design discussion first.

---

## 9. Deviations from the Suggested Directory Structure

None yet. Current structure matches the structure specified during initialization. Any future deviation gets documented here at the time it's made.
