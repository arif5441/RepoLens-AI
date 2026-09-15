#!/bin/bash

echo "🚀 Starting Backend (FastAPI)..."
cd /var/www/html/repoLens-ai/backend || exit
.venv/bin/uvicorn app.main:app --reload &

echo "🚀 Starting Frontend (Angular)..."
cd /var/www/html/repoLens-ai/frontend || exit
node_modules/.bin/ng serve &

wait

echo "🚀 All processes finished"

# ./run.sh
