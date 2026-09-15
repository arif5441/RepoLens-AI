# FEATURE.md — RepoLens AI Roadmap

Status legend: `[ ]` Planned · `[~]` In progress · `[x]` Completed

Nothing is marked complete until implemented and tested. This file is updated at the end of every feature (see `CLAUDE.md` §19).

**Note on phase numbering**: the original roadmap had Phase 3 = "Repository Ingestion". During execution, a "MySQL Vector Storage" phase was built and driven as "Phase 3" in conversation before repository ingestion — the natural build order (you need somewhere to put vectors before you need to ingest a repo to generate them from). This file has been renumbered to match what was actually built, rather than leaving the doc and reality out of sync. Phases below reflect the real order.

---

## Phase 0 — Foundation

- [x] Project directory structure
- [x] `CLAUDE.md`, `FEATURE.md`, architecture doc
- [x] Backend configuration management (env vars, settings module — `app/core/config.py`)
- [x] Logging setup (`app/core/logging.py`)
- [x] MySQL connection setup (`app/core/database.py`, SQLAlchemy engine + connectivity check)
- [x] FastAPI foundation (app factory in `app/main.py`, `GET /health` endpoint)
- [x] Angular foundation (project scaffold, app shell with header, dashboard route)
- [x] `LLMProvider` abstraction + `OllamaProvider` (availability/model-list check only — no generation yet)
- [x] Angular `ApiService` + `HealthService`, reusable `StatusIndicatorComponent`
- [x] `run.sh` — starts backend + frontend (kept deliberately simple per user preference — no env checks/cleanup trap, just cd + start + wait)
- [x] Backend tests (config, database, health endpoint) — 4 passing
- [x] Frontend tests (app shell, health service, dashboard component) — 6 passing

## Phase 1 — LLM Foundation

- [x] Ollama integration — `OllamaProvider.chat()` implemented (`app/llm/ollama_provider.py`), calls `POST /api/chat`
- [x] Model configuration — `OLLAMA_MODEL`, `OLLAMA_CHAT_TIMEOUT_SECONDS`, `LLM_TEMPERATURE` in `.env`/`.env.example`, nothing hard-coded. Default: `phi3:mini`
- [x] `LLMProvider` abstraction + `OllamaProvider` (base built in Phase 0, `chat()` added this phase)
- [x] Prompt abstraction/builder module (`app/llm/prompts.py` — system + user message construction)
- [x] LLM service layer (`app/services/llm_service.py`) — routes stay thin, service owns prompt building + logging + response normalization
- [x] Typed error hierarchy (`app/llm/exceptions.py`) mapped to HTTP status codes via a FastAPI exception handler (`app/api/error_handlers.py`) — 503 unavailable/model-not-found, 504 timeout, 502 other
- [x] `POST /api/v1/llm/chat` endpoint, request/response schemas (`app/schemas/llm.py`)
- [x] Angular `LlmService` + `LlmPlaygroundComponent` (`/playground` route) — UI5 web components, loading/success/error/empty states, disabled submit while loading
- [x] Backend tests: schema validation, service (mocked provider), provider (mocked httpx), route (dependency-overridden), plus a live integration test — 19 backend tests
- [x] Frontend tests: `LlmService` request shape, playground loading/success/error states — 12 frontend tests
- [x] **Real live round trip against a running Ollama — verified 2026-09-15.** Ollama 0.34.0, `phi3:mini` pulled (2.2GB). "Explain dependency injection in one paragraph." returned a coherent real answer in ~13.9s (CPU-only inference).
- LangChain was **not** introduced this phase — direct `httpx` calls to Ollama's REST API were sufficient. Revisit only if a later phase shows a concrete gap plain code doesn't cover.

## Phase 2 — Embeddings

- [x] `EmbeddingProvider` abstraction + `LocalEmbeddingProvider` (`app/embeddings/{base,local_provider}.py`) — sentence-transformers, model loaded once per process (`lru_cache`), not per request
- [x] Model configuration — `EMBEDDING_MODEL`, `EMBEDDING_DEVICE`, `EMBEDDING_NORMALIZE`. Default: `sentence-transformers/all-MiniLM-L6-v2`
- [x] Embedding generation service (`app/services/embedding_service.py`) — delegates to provider, computes pairwise cosine similarity, normalizes into response schema
- [x] Cosine similarity utility (`app/embeddings/similarity.py`) — pure Python
- [x] Typed error hierarchy (`app/embeddings/exceptions.py`) mapped to HTTP status — 503 model unavailable, 400 bad input, 502 other
- [x] `POST /api/v1/embeddings/test` diagnostic endpoint (in-memory only, no storage) — returns model/dimension/count/full vectors/pairwise similarities/duration
- [x] Angular `EmbeddingService` + `EmbeddingsPlaygroundComponent` (`/embeddings` route) — dynamic text rows (2-8), similarity results table sorted by score
- [x] Backend tests: similarity function, provider (mocked model), service (mocked provider), route, schema validation, plus a real (no-mock) integration test proving related text ranks above unrelated text — 44 backend tests
- [x] Frontend tests: `EmbeddingService` request shape, playground add/remove rows, loading/success/error states — 18 frontend tests
- [x] **Real embedding generation verified 2026-09-15.** `sentence-transformers/all-MiniLM-L6-v2` cached (2.2GB total incl. torch, ~90MB model itself). "calculate employee salary" ↔ "compute payroll amount" = **0.701**; ↔ "weather forecast for tomorrow" = **0.057**.
- LangChain was **not** introduced this phase — direct sentence-transformers calls were sufficient.

## Phase 3 — MySQL Vector Storage

- [x] Database design — `embeddings` table: `id`, `content`, `source_ref` (nullable, open-ended pointer for future code-chunk linkage), `model`, `dimension`, `vector` (JSON), `extra_metadata` (JSON, nullable), `created_at`, `updated_at`. Index on `(model, dimension)`. Not the final repository/code-chunk schema — deliberately generic, per scope.
- [x] Migration tooling decided: **Alembic** (`backend/alembic/`). `alembic revision --autogenerate` + `alembic upgrade head` — resolves the "TBD" left open in Phase 0.
- [x] Vector storage representation: MySQL `JSON` column (array of floats) — this MySQL (8.0.46) has no native `VECTOR` type (that's 9.0+/HeatWave-only). Documented as a deliberate, revisitable decision, not an oversight.
- [x] `EmbeddingRepository` (`app/repositories/embedding_repository.py`) — `save`, `get`, `delete`, `list_by_model`. All DB access isolated here; no raw SQLAlchemy elsewhere.
- [x] `RepositoryError` (`app/repositories/exceptions.py`) — wraps `SQLAlchemyError`, mapped to `503` with a generic "database unavailable" message (never leaks table/column/credential detail to the client — full detail logged server-side only)
- [x] `EmbeddingService` extended: `store_embeddings()` (embed + persist), `search_similar()` (embed query + brute-force cosine similarity over stored vectors, scoped to one model), `get_embedding()`, `delete_embedding()`. Existing `embed_and_compare()` (Phase 2, in-memory only) untouched.
- [x] Similarity search: **brute-force in Python**, not SQL — fetch all stored vectors for the query's model (`list_by_model`), compute cosine similarity in-process, sort, take top-N. No ANN indexing (see architecture doc §5 for why this is fine at this scale).
- [x] API: `POST /api/v1/embeddings/store`, `POST /api/v1/embeddings/search`, `GET /api/v1/embeddings/{id}`, `DELETE /api/v1/embeddings/{id}` — all diagnostic-tier, not the final ingestion/retrieval API
- [x] `get_db()` FastAPI dependency (`app/core/database.py`) — yields a `Session`, commits on success, rolls back on exception
- [x] Backend tests: repository (against real local MySQL, each test rolled back — no separate test DB needed at this scale), migration/schema verification, service (mocked repo+provider), route (dependency-overridden), a database-error-doesn't-leak-detail test — 66 backend tests total (22 new)
- [x] **Real end-to-end verified 2026-09-15.** Stored 3 real texts via `/store` → real MySQL rows (JSON vectors, 384-dim) → `/search` for "payroll salary math" ranked "compute payroll amount" (0.81) and "calculate employee salary" (0.79) above "weather forecast for tomorrow" (0.06) → `/get` and `/delete` confirmed (404 after delete). Phase 1 (LLM chat) and Phase 2 (`/test` in-memory embedding) regression-checked, both still work.
- No frontend UI added this phase (not requested — backend/storage focused).

## Phase 4 — Repository Ingestion

- [x] GitHub repository URL input + validation — `app/ingestion/url_parser.py`, regex-based, accepts `https://github.com/owner/repo` (+ optional `www.`, `.git`, trailing slash), rejects everything else including non-GitHub hosts
- [x] Repository access: **GitHub REST API + raw.githubusercontent.com over HTTPS — no clone, no git process, no local filesystem writes.** `app/ingestion/github_client.py` (`get_default_branch`, `get_tree` via the recursive git-trees API, `get_raw_content`). See `docs/architecture/overview.md` §4e for why this was chosen over cloning.
- [x] File discovery — full recursive tree listing in one API call (`git/trees/{branch}?recursive=1`); `truncated` flag from GitHub surfaced to the caller if the repo is too large for one response
- [x] Filtering rules (`app/ingestion/filters.py`, allowlist-based, extensible via one lookup table, not scattered checks): excludes `.git/`, `node_modules/`, `vendor/`, `dist/`, `build/`, `coverage/`, `.cache/`, `__pycache__/`, `.venv/`, `venv/`, `.idea/`, `.vscode/`, `target/`, `bin/`, `obj/`; excludes lockfiles and minified/generated files; excludes binary extensions (images/video/audio/archives/executables); **includes only** an explicit extension allowlist (`.py .php .js .jsx .ts .tsx .java .cs .go .rb .rs .cpp .cc .cxx .hpp .c .h .json .yaml .yml .xml .md`) — unrecognized extensions are excluded by default, not included by default
- [x] Safety limits, all configurable via `.env` — `INGESTION_MAX_FILES` (300), `INGESTION_MAX_FILE_SIZE_BYTES` (200KB/file), `INGESTION_MAX_TOTAL_SIZE_BYTES` (20MB total). Non-UTF-8 content (binary masquerading as a text extension) detected and skipped at decode time, never crashes ingestion.
- [x] Language detection — extension → language label lookup table (`detect_language`), not real parsing; e.g. `.py`→`python`, `.ts`/`.tsx`→`typescript`
- [x] Internal data model (`app/ingestion/models.py`) — `SourceFile` (path, language, content, size_bytes, repository, ref) and `IngestionResult` (counts + skip-reason breakdown + file list). Plain dataclasses, not persisted — no DB table this phase (scope explicitly excluded it; Phase 5 will decide what gets stored once chunking exists)
- [x] `RepositoryIngestionService` — implemented as `app/services/ingestion_service.py` (function-based, matching the existing `llm_service`/`embedding_service` style rather than a class, since there's no per-request state to hold)
- [x] Typed error hierarchy (`app/ingestion/exceptions.py`) mapped to HTTP status — 400 invalid URL, 404 not found/private (GitHub can't distinguish the two without auth), 429 rate limited, 502 other GitHub errors
- [x] `POST /api/v1/repositories/ingest` — request `{url, include_content?}`, response has repository/branch/counts/skip-reason breakdown/total size/truncated flag/file list. `include_content` defaults `false` to keep responses small; set `true` for small repos when the content itself is needed for inspection.
- [x] Angular `IngestionService` + `RepositoryIngestionComponent` (`/ingest` route) — URL input, summary panel, skipped-reasons breakdown, included-files table, loading/success/error/empty states
- [x] Backend tests: URL parsing, filter rules (directories/lockfiles/binaries/size/language), GitHub client (mocked httpx — 404/403/timeout/non-UTF-8), ingestion service (fake client — nested dirs, tree-vs-blob, file-count cap, size-budget cap, language detection), API route (dependency-overridden), plus real integration tests against `octocat/Spoon-Knife` (skips automatically if GitHub is unreachable) — **119 backend tests total** (53 new)
- [x] Frontend tests: `IngestionService` request shape, component enable/disable logic, success/error rendering — 23 frontend tests total (4 new)
- [x] **Real ingestion verified 2026-09-15** against `octocat/Spoon-Knife`: 3 files discovered, `README.md` included (markdown, 780 bytes, real content fetched and returned), `index.html`/`styles.css` correctly excluded as unsupported extensions. Also verified: 404 for a nonexistent repo, 400 for an invalid URL — both through the live running API.
- No code chunking, embeddings, or vector storage integration this phase — output is filtered source files only, ready for Phase 5.

## Phase 5 — Code Chunking

- [x] Code-aware chunking (`app/chunking/chunker.py`) — regex-based boundary detection per language family (def/class for Python, function/class for JS/TS, func for Go, fn/struct/enum for Rust, def/class/module for Ruby, function/class for PHP, class/interface for Java/C#), not full AST parsing (documented tradeoff — see architecture doc). Falls back to fixed-size line chunking for languages without a reliable pattern (C/C++, JSON/YAML/XML/Markdown) or files with no detected boundary.
- [x] Function/class/module metadata per chunk — `CodeChunk.symbol_name` (`app/chunking/models.py`)
- [x] Start/end line tracking — exact, 1-indexed, always present on every chunk
- [x] Chunk relationships — `repository` + `path` + `chunk_index` identify a chunk's parent file and position; no separate "sibling" graph built (not needed by anything downstream yet)
- [x] 11 backend tests covering Python/JS/Go boundary detection, large-function sub-splitting, fallback chunking, trailing-blank-line handling

## Phase 6 — Retrieval

- [x] `embeddings` table extended (Alembic migration `b0636226f4c7`) with `repository`, `file_path`, `start_line`, `end_line`, `symbol_name` — dedicated indexed columns, not JSON, since repository-scoped filtering is a core always-used query pattern (see architecture doc §4g)
- [x] `EmbeddingRepository` extended: `list_by_repository`, `list_by_repository_and_path`, `list_indexed_repositories`, `delete_by_repository`
- [x] `repository_service.py` — `index_repository()` wires ingestion (Phase 4) + chunking (Phase 5) + embedding (Phase 2) + storage (Phase 3) into one pipeline; re-indexing replaces previous chunks rather than duplicating
- [x] Semantic retrieval — `search_repository()`: embed query, brute-force cosine similarity over one repository's stored chunks, ranked
- [x] Metadata filtering — scoped by repository + embedding model (cross-model comparison is meaningless, same rule as Phase 3)
- [x] Retrieval ranking — sorted by cosine similarity descending
- [ ] Hybrid retrieval (keyword + semantic) — not implemented; not justified yet (no evaluation result has shown pure semantic retrieval missing obvious keyword matches)
- [x] API: `POST /api/v1/repositories/index`, `GET /api/v1/repositories`, `POST /api/v1/repositories/search`
- [x] 18 new backend tests (repository methods, service with fakes, routes with dependency overrides)
- [x] **Real verified 2026-09-15** against `trekhleb/learn-python` (73 files, 237 chunks, real GitHub + real embeddings + real MySQL): searching "how do generators work" correctly ranked `test_generators.py` top 3 results, similarity 0.50/0.49/0.41 vs. unrelated files scoring lower.

## Phase 7 — RAG

- [x] Query processing — reuses `search_repository()`, no separate query-rewriting step (not needed at this scope)
- [x] Context construction — `app/rag/context.py:build_context()`, numbered `[N] path (lines A-B)` blocks, character-budget-aware (drops lowest-similarity chunks first, always keeps at least one)
- [x] Prompt construction — `app/rag/prompts.py:build_rag_messages()`, system prompt explicitly instructs the model to treat retrieved code as **data, not instructions** (prompt-injection mitigation — see Security Rules) and to cite `[N]` labels
- [x] LLM response generation — via existing `LLMProvider`/`OllamaProvider` (Phase 1), unchanged
- [x] Citation/evidence extraction — every citation carries file path, exact line range, similarity score, and the actual chunk content (so the UI can show real source, not just a pointer)
- [x] "Insufficient evidence" fallback path — `rag_service.py`: if no retrieved chunk clears `RAG_MIN_SIMILARITY` (default 0.2), the LLM is never called; a fixed, honest "could not find enough evidence" response is returned instead (`grounded: false`)
- [x] API: `POST /api/v1/repositories/ask`
- [x] 11 backend tests (context budget behavior, service with fakes incl. the insufficient-evidence path proving the LLM is never called, routes)
- [x] **Real verified 2026-09-15** against `trekhleb/learn-python`: asked "How do generators work in this codebase? Give a code example." — got a correct, grounded answer quoting the real `lottery()`/`test_generators()` functions with accurate citations (similarity 0.49/0.47/0.39/0.25/0.25), `grounded: true`. **Took 112.6s** on this CPU-only machine (longer prompt than Phase 1's simple chat) — `OLLAMA_CHAT_TIMEOUT_SECONDS` raised from 60 to 180 after the first attempt genuinely timed out. This is a real, load-bearing hardware limitation, not a bug — see Performance notes below.

## Phase 8 — Code Intelligence

- [x] Code explanation (single file) — `POST /api/v1/repositories/explain`: gathers all stored chunks for one file, asks the LLM to explain it, same prompt-injection-safe pattern as RAG
- [ ] Architecture analysis (cross-file/module relationships) — **not implemented**. Would need real cross-file reference resolution (imports, call graphs), which the current line-based chunker doesn't extract. Honest scope cut for this session.
- [ ] Documentation generation — **not implemented**. Could be built cheaply on top of `/explain` (ask for docstring-style output instead of prose) but wasn't built — no concrete use case drove it yet.
- [ ] Code relationship analysis (call graphs, imports) — **not implemented**. Needs real per-language parsing beyond the current regex-boundary chunker.
- [ ] Potential issue detection — **not implemented**. Would be another LLM-prompt variant on `/explain`'s pattern, but asking an LLM to "find bugs" without a real static-analysis pass tends to hallucinate issues — didn't want to ship something that looks authoritative but isn't grounded the way RAG answers are.
- [x] 6 backend tests (service with fakes, route with dependency overrides)

## Phase 9 — Evaluation

- [x] Evaluation dataset — `evaluation/datasets/learn_python.json`, 10 real question/expected-file cases against `trekhleb/learn-python` (expected files confirmed by inspecting the real repo tree, not guessed)
- [x] Retrieval evaluation — `evaluation/eval_retrieval.py`: indexes the repo for real, runs every question through real search, checks whether the expected file appears in the top-5
- [x] Answer evaluation — for a subset of cases (`run_ask: true`, 2 of 10 — full RAG is slow on CPU, see Phase 7 notes), also runs the real `/ask` pipeline and checks `grounded == true`
- [x] Citation correctness checks — for the same subset, checks whether at least one citation's file matches the expected file
- [x] Measurable metrics — printed to stdout *and* written as structured JSON to `evaluation/results/eval_<timestamp>.json` (gitignored — these are run artifacts, not source). No dashboard UI (out of scope) — a script you run and read, consistent with "verify for real" throughout this project.
- [x] **Real run 2026-09-15**: **retrieval hit rate 100% (10/10)**, **answer grounded rate 100% (2/2)**, **citation correctness 100% (2/2)**. Small sample size — 10 questions against one repo — stated as what it is, not oversold as a comprehensive benchmark.
- Not a CI gate — a full run takes several minutes (indexing + 2 real LLM calls) and isn't meant to block every commit; it's a report you run manually when retrieval/RAG behavior changes.

## Phase 10 — Angular UI

- [x] Dashboard — existing (Phase 0), unchanged
- [x] Repository management — `RepositoryManagementComponent` (`/repositories`): index a new repo (calls real `/index`), lists all indexed repos with chunk counts and last-indexed time
- [ ] Indexing status view — **not implemented as a separate live-progress view**. `/index` is a single synchronous call (the UI shows a busy indicator + final summary, not a step-by-step progress stream) — no background job queue exists to report incremental progress against, and adding one wasn't justified at this scale (a 73-file repo indexes in ~35s).
- [x] Chat/question interface — `ChatComponent` (`/chat`): repository picker, question box, conversation history, grounded/citation display, explicit "this runs on a local CPU model, can take a minute or two" notice (honest about real latency rather than hiding it)
- [x] Source code viewer — folded into the chat UI rather than a separate page: each citation is expandable inline to show the exact cited source (file path, line range, real content) — satisfies "see the cited code" without a separate full-repo file browser (which would need its own file-tree API not built this phase)
- [ ] Architecture view — **not implemented**. Depends on Phase 8's architecture analysis, which isn't built.
- [ ] Documentation view — **not implemented**. Same reasoning — depends on unbuilt Phase 8 documentation generation.
- [ ] Evaluation view — **not implemented**. `evaluation/eval_retrieval.py` results are file-based (see Phase 9), not surfaced in the UI. Would be straightforward to add (read the latest `evaluation/results/*.json`) but wasn't asked for as a concrete need yet.
- [x] 12 new frontend tests (repository service, repository management component, chat component) — **35 frontend tests total**
- [x] Verified live via screenshots against the real running stack with real indexed data (`trekhleb/learn-python`, 237 chunks) — repository list renders real data, chat page's repository dropdown populates from the real API

## Phase 11 — Production Quality

- [x] Backend test suite — **164 tests** (unit + real-DB + real-external-service integration, consistently across every phase)
- [x] Frontend component tests — **35 tests**
- [x] Logging/observability pass — every new service logs at INFO on success (counts/durations/models, never content) and WARNING/ERROR on failure; reviewed for consistency with the pattern established in Phase 1
- [x] Error handling audit — every new exception type (chunking has none — pure functions, can't fail; ingestion/retrieval/RAG/code-intelligence errors) is typed and mapped to an HTTP status via `error_handlers.py`, following the one established pattern rather than inventing new ones per feature
- [x] Security review — see dedicated section in `docs/architecture/overview.md` §10. Key points: prompt-injection mitigation in RAG/explain prompts (retrieved code treated as data, not instructions, explicitly in the system prompt); no local filesystem writes anywhere in ingestion (GitHub API only); resource limits (file count/size, chunk size) unchanged from Phase 4; **known gap, documented not fixed**: `/index`, `/search`, `/ask` have no per-caller rate limiting of their own, so a misbehaving caller could exhaust GitHub's rate limit or run up CPU time — acceptable for a single-developer local tool without auth, would need addressing before any multi-user or public deployment.
- [x] Performance pass — real observed numbers, not estimates: indexing `trekhleb/learn-python` (73 files) took ~33s; a 5-chunk-context RAG answer took ~113s on this CPU-only machine; a 3-chunk one took ~98s. Documented in the architecture doc as this machine's numbers, not universal claims.
- [x] GitHub Actions CI — `.github/workflows/ci.yml`: backend job (MySQL 8.0 service container, `alembic upgrade head`, `pytest`) + frontend job (`ng build`, `ng test --browsers=ChromeHeadless`). Ollama-dependent and GitHub-rate-limit-dependent tests skip gracefully in CI, same as locally. **Not yet run through actual GitHub Actions** — validated by YAML syntax check and because every command in it is the same one already verified working locally throughout this session; will only be proven for real the first time it runs on a push (git operations are the user's to do, per instruction).
- [x] Documentation pass — this file, `CLAUDE.md`, `docs/architecture/overview.md`, `README.md` all updated to match reality.

## Phase 12 — Public Release

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

Phases 5–11 are complete and verified (with honest partial scope on Phase 8 code intelligence, Phase 9 evaluation, and Phase 10 UI views — see each phase's notes above for exactly what was and wasn't built). RepoLens now does real end-to-end grounded Q&A over a real indexed GitHub repository. Remaining: **Phase 12 — Public Release** (README polish, screenshots, demo, architecture diagrams, setup guide, contribution guide, license, tagged release) — not started, not requested this session.
