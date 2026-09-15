# RepoLens AI

Codebase intelligence and explainable RAG system. Index a public GitHub repository, ask questions about its source code, get answers grounded in retrieved code with file/function/line-level citations.

## Status

**Early development — initialization phase.** No functional features implemented yet. See [FEATURE.md](FEATURE.md) for the full roadmap and current progress.

## Problem

Understanding an unfamiliar codebase is slow. Grepping and manual reading don't surface cross-file relationships or intent. Generic LLM chat (paste-and-ask) hallucinates APIs and can't point to real code locations.

## Solution

RepoLens indexes a repository's source code into searchable, code-aware chunks (function/class-level, not arbitrary text splits), retrieves the most relevant chunks for a question via semantic search, and asks a local LLM to answer using only that retrieved evidence — citing exact file, function, and line ranges. When there isn't enough evidence, it says so instead of guessing.

## Planned Features

- Index any public GitHub repository
- Ask natural-language questions about the codebase
- Grounded answers with source citations (file/function/line)
- Code explanation, architecture analysis, and documentation generation
- Evaluation system to measure retrieval and answer quality
- Enterprise-style Angular UI (SAP Fiori-inspired) for repo management, chat, source viewing, and evaluation

Full phased roadmap: [FEATURE.md](FEATURE.md)

## Architecture

```text
Angular (Fiori-style UI)
   ↓
FastAPI
   ↓
Application Services
   ↓
RAG Pipeline (retrieve → rank → context → prompt → LLM)
   ↓
MySQL (app data + embeddings)
   ↓
Ollama (local LLM)
```

Full architecture document, data flow, database design, and AI concept explanations: [docs/architecture/overview.md](docs/architecture/overview.md)

## Technology Stack

- **Backend**: Python, FastAPI, LangChain, Pydantic, sentence-transformers, Ollama
- **Database**: MySQL
- **Frontend**: Angular, TypeScript, UI5 Web Components, Tailwind CSS

See [CLAUDE.md](CLAUDE.md) for full stack rationale and prohibited technologies.

## Free / Local-First Philosophy

RepoLens runs entirely on local, free/open-source models by default: Ollama for the LLM, a local embedding model for semantic search, MySQL for storage. No paid API key is required to use the core product. Any future optional paid provider would sit behind a provider abstraction and remain strictly opt-in.

## Installation

*Not available yet — application is not implemented.* This section will be filled in once Phase 0 (foundation) is complete.

## Demo

*Planned for Phase 11 (public release): screenshots and a demo video/recording will be added here.*

## License

See [LICENSE](LICENSE).
# RepoLens-AI
