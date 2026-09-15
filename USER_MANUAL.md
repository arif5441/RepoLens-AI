# RepoLens AI — User Manual

## Who is this for

Anyone exploring an unfamiliar public GitHub codebase and wanting grounded, cited answers instead of guesswork — developers onboarding to a new repo, reviewers, students. Runs fully local, no paid API key needed.

## Prerequisites

- Python 3.11+
- Node.js (LTS)
- MySQL 8
- [Ollama](https://ollama.com) installed and running

## 1. One-time setup

1. Clone the repo:
   ```bash
   git clone <repo-url> repolens-ai && cd repolens-ai
   ```
2. Copy env file and fill MySQL credentials:
   ```bash
   cp .env.example .env
   ```
3. Install backend deps:
   ```bash
   python3 -m venv backend/.venv
   backend/.venv/bin/pip install -r backend/requirements.txt
   ```
4. Install frontend deps:
   ```bash
   npm install --prefix frontend
   ```
5. Pull the LLM model:
   ```bash
   ollama pull phi3:mini
   ```
6. Create database schema:
   ```bash
   cd backend && .venv/bin/alembic upgrade head && cd ..
   ```

## 2. Start the app

```bash
./run.sh
```

Starts backend (`http://localhost:8000`) + frontend (`http://localhost:4200`) together. Wait for both to finish booting (first run also downloads embedding model, ~30s).

## 3. Index a repository

1. Open `http://localhost:4200/repositories`
2. Paste a public GitHub URL (e.g. `https://github.com/trekhleb/learn-python`)
3. Click Index
4. Wait — pulls files, chunks code, generates embeddings, stores in MySQL. Small repo ≈ 30–40s.
5. Confirm it appears in the indexed-repos list with a chunk count.

## 4. Ask questions

1. Open `http://localhost:4200/chat`
2. Pick the indexed repository from the dropdown
3. Type a question about the code (e.g. "How do generators work in this codebase?")
4. Submit and wait — CPU-only inference, expect **~100–115 seconds** for a grounded answer
5. Read the answer. Each citation is expandable — click to see the exact file, line range, and real source snippet backing the claim
6. If evidence is too weak, app says so instead of guessing ("could not find enough evidence") — this is expected, correct behavior, not a bug

## 5. Optional diagnostic pages

Not needed for normal use — useful for debugging pipeline stages individually.

| Page | Purpose |
|---|---|
| `/playground` | Raw LLM chat, no repo context |
| `/embeddings` | Test embedding + similarity, nothing stored |
| `/ingest` | Test file discovery/filtering only, nothing stored |

## 6. Stopping the app

`Ctrl+C` in the terminal running `./run.sh` — stops backend + frontend both.

## Troubleshooting

- **Chat takes 2+ minutes**: normal on CPU-only machine, see README "A note on speed".
- **Indexing fails with 404**: repo URL wrong or repo is private — only public repos supported.
- **Indexing fails with 429**: GitHub rate limit hit (60 req/hr unauthenticated) — set `GITHUB_TOKEN` in `.env`.
- **LLM errors (503)**: Ollama not running, or model not pulled — run `ollama pull phi3:mini`.
