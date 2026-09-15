# FEATURE.md — RepoLens AI Roadmap

Status legend: `[ ]` Planned · `[~]` In progress · `[x]` Completed

Nothing is marked complete until implemented and tested. This file is updated at the end of every feature (see `CLAUDE.md` §19).

---

## Phase 0 — Foundation

- [x] Project directory structure
- [x] `CLAUDE.md`, `FEATURE.md`, architecture doc
- [ ] Backend configuration management (env vars, settings module)
- [ ] Logging setup
- [ ] MySQL connection setup
- [ ] FastAPI foundation (app factory, health endpoint)
- [ ] Angular foundation (project scaffold, base layout, routing shell)

## Phase 1 — LLM Foundation

- [ ] Ollama integration
- [ ] Model configuration (which local model, params)
- [ ] `LLMProvider` abstraction + `OllamaLLMProvider`
- [ ] Prompt abstraction/builder module
- [ ] Basic LLM request/response round trip (smoke test endpoint)

## Phase 2 — Embeddings

- [ ] `EmbeddingProvider` abstraction + local implementation (sentence-transformers)
- [ ] Embedding generation service
- [ ] Embedding storage design in MySQL

## Phase 3 — Repository Ingestion

- [ ] GitHub repository URL input + validation
- [ ] Repository download/clone (safe, depth-limited, no hook execution)
- [ ] File discovery
- [ ] Ignored-file rules (`.gitignore`-aware, binary detection, size limits)
- [ ] Language detection
- [ ] Source parsing
- [ ] Repository/file metadata persistence

## Phase 4 — Code Chunking

- [ ] Code-aware chunking (function/class boundaries, not naive fixed-size)
- [ ] Function/class/module metadata per chunk
- [ ] Start/end line tracking
- [ ] Chunk relationships (parent file, sibling chunks)

## Phase 5 — Retrieval

- [ ] Semantic retrieval over stored embeddings
- [ ] Similarity calculation (MySQL-based, no dedicated vector DB)
- [ ] Metadata filtering (by language, file, repo)
- [ ] Retrieval ranking
- [ ] Hybrid retrieval (keyword + semantic) — only if justified by evaluation results

## Phase 6 — RAG

- [ ] Query processing
- [ ] Context construction from retrieved chunks
- [ ] Prompt construction (question + context + citation instructions)
- [ ] LLM response generation
- [ ] Citation/evidence extraction and attachment to answer
- [ ] "Insufficient evidence" fallback path

## Phase 7 — Code Intelligence

- [ ] Code explanation (single function/file)
- [ ] Architecture analysis (cross-file/module relationships)
- [ ] Documentation generation
- [ ] Code relationship analysis (call graphs, imports)
- [ ] Potential issue detection

## Phase 8 — Evaluation

- [ ] Evaluation dataset (question/expected-evidence pairs)
- [ ] Retrieval evaluation (precision/recall of retrieved chunks)
- [ ] Answer evaluation (correctness, groundedness)
- [ ] Citation correctness checks
- [ ] Measurable metrics dashboard/report

## Phase 9 — Angular UI

- [ ] Dashboard
- [ ] Repository management (add/list/remove indexed repos)
- [ ] Indexing status view
- [ ] Chat/question interface
- [ ] Source code viewer (with cited line highlighting)
- [ ] Architecture view
- [ ] Documentation view
- [ ] Evaluation view

## Phase 10 — Production Quality

- [ ] Backend test suite (unit + integration)
- [ ] Frontend component tests
- [ ] Logging/observability pass
- [ ] Error handling audit
- [ ] Security review (path traversal, injection, resource limits, prompt injection)
- [ ] Performance pass (ingestion + retrieval latency)
- [ ] GitHub Actions CI
- [ ] Documentation pass

## Phase 11 — Public Release

- [ ] README polish
- [ ] Screenshots
- [ ] Demo (video or hosted)
- [ ] Architecture diagrams
- [ ] Setup guide
- [ ] Contribution guide
- [ ] License finalized
- [ ] Tagged release

---

## Next Recommended Step

Phase 0 remainder: backend config/logging/MySQL connection + FastAPI skeleton, then Angular scaffold. See `docs/architecture/overview.md` for the target layout before starting.
