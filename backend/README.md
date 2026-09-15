# RepoLens AI — Backend

Python/FastAPI backend. Not yet implemented — see [FEATURE.md](../FEATURE.md) Phase 0.

Layout:

```text
app/
├── api/            FastAPI routes (thin — validate, call service, return response)
├── core/           config, logging, app factory
├── models/         ORM/DB models
├── schemas/        Pydantic request/response contracts
├── services/       application/domain logic
├── repositories/   data-access layer
├── ingestion/       repository cloning, file discovery, parsing
├── embeddings/      embedding provider + generation
├── retrieval/       similarity search, ranking, filtering
├── rag/             context construction, prompt building, orchestration
├── llm/             LLM provider abstraction (Ollama)
└── main.py          FastAPI entrypoint
```

See [docs/architecture/overview.md](../docs/architecture/overview.md) for the full pipeline design.
