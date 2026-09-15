#!/bin/bash
#
# RepoLens AI — local dev start script.
# NOTE: backend/frontend not implemented yet (Phase 0). Commands below are
# the target shape — update once backend/app/main.py and frontend exist.

echo "🚀 Starting Backend (FastAPI)..."
cd /var/www/html/repoLens-ai/backend || exit
uvicorn app.main:app --reload &

echo "🚀 Starting Frontend (Angular)..."
cd /var/www/html/repoLens-ai/frontend || exit
ng serve &

wait

echo "🚀 All processes finished"

# ./run.sh
