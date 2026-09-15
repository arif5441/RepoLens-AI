# CLAUDE.md — RepoLens AI

Persistent project context. Read before implementing any feature. Keep updated when architecture/decisions change.

## 1. Project Purpose

RepoLens AI is a codebase intelligence and explainable RAG (Retrieval-Augmented Generation) system. A developer gives it a public GitHub repository URL; it indexes the source code and answers natural-language questions about it. Every answer must be grounded in retrieved source code and cite file/function/line-level evidence. Not a chatbot wrapper — a retrieval-first system that refuses to answer when evidence is insufficient.

Portfolio project. Must demonstrate production engineering judgment, not just "I called an LLM API."

## 2. Project Philosophy

- Small, effective, technically credible, understandable, maintainable. No gold-plating.
- Retrieval quality is the product. LLM is the last mile, not the whole pipeline.
- Free/local-first: runs entirely on local models (Ollama + local embeddings) and MySQL. No paid API required to use the core product.
- Every technology choice has a stated reason. No buzzword-driven architecture.
- Grounded answers over confident hallucination. "I could not find enough evidence" is a valid, preferred answer.

## 3. Developer Context

Working with an experienced backend/frontend/API/database engineer (REST, HTTP, MySQL, Angular, PHP/Laravel, Node.js, TypeScript, design patterns, production code org). New to AI/ML/LLM/RAG/LangChain/embeddings/vector search/evaluation.

Rule for every new AI concept introduced in this project: explain (1) what it is, (2) why RepoLens needs it, (3) how it works in this architecture, (4) the code being written. Keep explanations practical, tied to this codebase — not generic ML theory. Do not explain basic software engineering concepts (REST, HTTP, Git, etc).

## 4. Technology Stack

### Backend
- Python, FastAPI
- LangChain (orchestration glue for RAG pipeline — not a replacement for our own retrieval/service logic)
- Pydantic (request/response/schema validation)
- sentence-transformers (or equivalent local embedding library)
- Ollama (local LLM execution)

### Database
- MySQL (application data + embedding storage)

### Frontend
- Angular, TypeScript
- UI5 Web Components / SAP Fiori-inspired enterprise design language
- Tailwind CSS only where it doesn't fight the Fiori look

### Explicitly NOT used unless a documented architectural reason forces reconsideration
- Docker
- Qdrant / Pinecone / Weaviate / any dedicated vector DB
- PostgreSQL
- Redis
- Any paid AI API as a hard dependency

If a new dependency is proposed, state the reason in `docs/architecture/overview.md` before adding it.

## 5. Coding Standards

- Strong typing everywhere: Python type hints + Pydantic models on the backend, strict TypeScript on the frontend.
- Meaningful names. No abbreviations that aren't domain-standard.
- Small, focused functions and modules. No giant files.
- No duplicated logic — extract shared code into services/utilities once a real second use appears (not preemptively).
- Config via environment variables, never hard-coded. `.env.example` always kept current.
- No hard-coded secrets, credentials, or paths (no `/var/www/...` assumptions).
- Logging over print statements. Structured where practical.

## 6. Architecture Rules

- Layered backend: `api` (FastAPI routes) → `services` (application/domain logic) → `repositories` (data access) → `models` (ORM/DB) with `schemas` (Pydantic I/O contracts) crossing the api/service boundary.
- `ingestion`, `embeddings`, `retrieval`, `rag`, `llm` are domain-specific pipeline modules, not dumping grounds — each owns one stage of the pipeline described in `docs/architecture/overview.md`.
- Provider abstractions for anything swappable: `LLMProvider` (→ `OllamaLLMProvider`), `EmbeddingProvider` (→ `LocalEmbeddingProvider`). Add interfaces only when a second implementation is plausible — don't abstract a single hardcoded call.
- Before implementing a feature, inspect the existing architecture and documentation. Reuse existing abstractions and components where appropriate. Do not duplicate functionality.
- Do not rewrite working code unnecessarily. Make the smallest clean change required for the feature.

## 7. Frontend Rules

- SAP Fiori / UI5-inspired enterprise design language: clean, professional, no flashy startup aesthetics, no gratuitous gradients/animations/gimmicks.
- Consistent spacing, accessible controls, responsive layout, clear information hierarchy.
- Professional data tables, dialogs/drawers where appropriate.
- Explicit loading, empty, and error states for every async view. Semantic status indicators (not just color — icon/text too).
- Component-based: reusable Angular components, no copy/paste screens.

## 8. Backend Rules

- FastAPI routes stay thin — validate input, call a service, return a typed response. No business logic in route handlers.
- Every endpoint has a typed request/response schema (Pydantic).
- Consistent API response structure across endpoints (success shape, error shape).
- Repository/data-access layer isolates MySQL/SQL specifics from services.

## 9. AI/LLM Rules

- LLM access always goes through `LLMProvider` abstraction — never call Ollama's API directly from a service.
- Embedding generation always goes through `EmbeddingProvider` abstraction.
- Prompts are constructed via a dedicated prompt-building module, not inline f-strings scattered across services — keep prompt engineering visible and reviewable in one place per use case.
- Never feed unsanitized repository content into a prompt without treating it as untrusted (prompt-injection risk from repo comments/strings — see Security Rules).

## 10. RAG Rules

The product is never `Question → LLM → Answer`. Always:

```text
Question → Retrieve relevant code → Rank/filter evidence → Build context → LLM → Grounded answer → Evidence/citations
```

- Retrieved code chunks must carry: repository, file path, language, class, function/method (where available), start line, end line, chunk ID.
- If retrieval returns insufficient/low-confidence evidence, the system must say so rather than let the LLM fabricate an answer.
- Every RAG answer that claims something about the code must be traceable to a cited chunk.

## 11. Database Rules

- MySQL is the single source of truth for application data AND embedding storage (no separate vector DB — see architecture doc for how vector search is done in MySQL).
- Schema changes go through migrations. Tooling: **Alembic** (decided Phase 3, `backend/alembic/`). Every schema change gets a migration — never hand-edit the database or rely on `Base.metadata.create_all()`.
- Vectors are stored as a MySQL `JSON` column (array of floats), not a native `VECTOR` type — this MySQL version (8.0) doesn't have one (that's MySQL 9.0+/HeatWave). Similarity is computed brute-force in Python, not in SQL. See architecture doc §5 for the full reasoning.
- No raw SQL string interpolation of user input — parameterized queries only.

## 12. Testing Rules

- Every important service gets tests eventually: ingestion, chunking, embedding, retrieval, RAG, API, frontend components, evaluation.
- AI output is not tested by exact string equality — use similarity/evaluation-appropriate assertions (see Phase 8, evaluation system).
- Do not claim a feature is tested until tests actually exist and pass.

## 13. Security Rules

RepoLens processes arbitrary public GitHub repositories — treat all repo content as untrusted input.

- Never execute code found in an indexed repository.
- Guard against: path traversal during file discovery, huge repos (resource exhaustion), binary files, secrets embedded in repo content (don't echo them back), malicious Git operations, prompt injection via source comments/strings/READMEs instructing the LLM to ignore instructions.
- Repository ingestion (Phase 4) uses the **GitHub REST API + raw content CDN over plain HTTPS** — no `git clone`, no local filesystem writes, no git process invocation at all. This sidesteps git-specific attack surface (hooks, submodules, symlinks, `.git` internals) entirely rather than needing to restrict it. File paths come from GitHub's API response, not local disk, so there's no local path to traverse.
- Ingestion enforces configurable limits (`INGESTION_MAX_FILES`, `INGESTION_MAX_FILE_SIZE_BYTES`, `INGESTION_MAX_TOTAL_SIZE_BYTES`) against resource exhaustion from huge/malicious repos, and a strict file-extension allowlist (`app/ingestion/filters.py`) rather than a denylist — unrecognized file types are excluded by default, not included by default.
- No secrets in code or Git history. `.env` never committed.

## 14. Git Rules

- Proper `.gitignore` from project init (venvs, node_modules, `.env`, IDE/OS files, logs, build output, generated data, local model/cache files).
- Never commit: `.env`, API keys, passwords, DB credentials, local model files, large generated embeddings, private repo data.

## 15. Documentation Rules

- `CLAUDE.md` (this file), `FEATURE.md`, `docs/architecture/overview.md` are the persistent project context — kept current, not aspirational.
- Any architecture or major decision change updates `docs/architecture/overview.md` in the same change.
- Do not document unimplemented features as if they exist.

## 16. Free/Local-First Requirement

- Default path must work with zero paid services: Ollama for LLM, local embedding model, MySQL for storage.
- Optional paid providers (if ever added) sit behind the provider abstractions and are opt-in — default app behavior never requires them.

## 17. UI/UX Requirements

See Frontend Rules (§7). Enterprise tool aesthetic, not consumer/startup.

## 18. Prohibited Technologies (unless explicitly approved + documented)

Docker, Qdrant, Pinecone, Weaviate, PostgreSQL, Redis, mandatory paid AI APIs, unnecessary microservices/queues/extra databases/frameworks.

## 19. Development Workflow

For every feature:

1. Read `CLAUDE.md`.
2. Read relevant parts of `FEATURE.md`.
3. Read `docs/architecture/overview.md`.
4. Inspect existing implementation.
5. Briefly explain the feature.
6. Explain any new AI concept involved (per §3).
7. Propose implementation approach.
8. Implement cleanly.
9. Add/update tests.
10. Run relevant tests.
11. Update documentation.
12. Update `FEATURE.md` status.
13. Report exactly what changed.

Do not skip documentation updates for architectural changes. Do not claim a feature complete until implemented and tested.
