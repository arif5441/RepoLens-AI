#!/usr/bin/env bash
#
# RepoLens AI — local development entry point.
#
# Current stage (Phase 0): backend/frontend are not implemented yet.
# This script validates the local environment and reports what's missing.
# Once Phase 0 lands, it will also start the backend and frontend.

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"

MISSING=0
WARN=0

pass() { printf '  [OK]   %s\n' "$1"; }
fail() { printf '  [FAIL] %s\n' "$1"; MISSING=$((MISSING + 1)); }
warn() { printf '  [WARN] %s\n' "$1"; WARN=$((WARN + 1)); }

echo "RepoLens AI — environment check"
echo "================================"

# --- .env ---
echo
echo "Configuration:"
if [[ -f "${ENV_FILE}" ]]; then
    pass ".env found"
else
    warn ".env not found — copy .env.example to .env and fill in local values"
fi

# --- Python ---
echo
echo "Python:"
if command -v python3 >/dev/null 2>&1; then
    PY_VERSION="$(python3 --version 2>&1)"
    pass "python3 found (${PY_VERSION})"
else
    fail "python3 not found — install Python 3.11+"
fi

if [[ -f "${PROJECT_ROOT}/backend/requirements.txt" ]]; then
    pass "backend/requirements.txt found"
else
    warn "backend/requirements.txt not found — backend not yet initialized"
fi

if [[ -d "${PROJECT_ROOT}/backend/.venv" ]]; then
    pass "backend virtualenv found at backend/.venv"
else
    warn "no virtualenv at backend/.venv — create one before running the backend"
fi

# --- Node / npm ---
echo
echo "Node.js:"
if command -v node >/dev/null 2>&1; then
    pass "node found ($(node --version))"
else
    fail "node not found — install Node.js LTS"
fi

if command -v npm >/dev/null 2>&1; then
    pass "npm found ($(npm --version))"
else
    fail "npm not found — install npm"
fi

if [[ -f "${PROJECT_ROOT}/frontend/package.json" ]]; then
    pass "frontend/package.json found"
else
    warn "frontend/package.json not found — Angular app not yet scaffolded"
fi

# --- MySQL ---
echo
echo "MySQL:"
if command -v mysql >/dev/null 2>&1; then
    pass "mysql client found"
else
    warn "mysql client not found on PATH — cannot verify connectivity from this script"
fi

if [[ -f "${ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    set -a; source "${ENV_FILE}"; set +a
    if command -v mysql >/dev/null 2>&1 && [[ -n "${MYSQL_HOST:-}" ]]; then
        if mysql -h "${MYSQL_HOST}" -P "${MYSQL_PORT:-3306}" -u "${MYSQL_USER:-}" \
            ${MYSQL_PASSWORD:+-p"${MYSQL_PASSWORD}"} -e "SELECT 1;" >/dev/null 2>&1; then
            pass "connected to MySQL at ${MYSQL_HOST}:${MYSQL_PORT:-3306}"
        else
            fail "could not connect to MySQL at ${MYSQL_HOST}:${MYSQL_PORT:-3306} — check credentials/service status"
        fi
    else
        warn "MySQL connectivity not verified (missing client or MYSQL_HOST in .env)"
    fi
else
    warn "MySQL connectivity not verified (.env missing)"
fi

# --- Ollama ---
echo
echo "Ollama:"
if command -v ollama >/dev/null 2>&1; then
    pass "ollama CLI found"
    OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
    if command -v curl >/dev/null 2>&1; then
        if curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
            pass "ollama server reachable at ${OLLAMA_URL}"
        else
            warn "ollama CLI found but server not reachable at ${OLLAMA_URL} — is 'ollama serve' running?"
        fi
    fi
else
    warn "ollama not found — install from https://ollama.com and pull a model"
fi

# --- Summary ---
echo
echo "================================"
if [[ ${MISSING} -gt 0 ]]; then
    echo "Environment check FAILED: ${MISSING} required dependency issue(s), ${WARN} warning(s)."
    echo "Resolve the [FAIL] items above before continuing."
    exit 1
fi

if [[ ${WARN} -gt 0 ]]; then
    echo "Environment check passed with ${WARN} warning(s)."
else
    echo "Environment check passed."
fi

echo
echo "Backend and frontend are not implemented yet (Phase 0 in progress)."
echo "This script will start both once they exist. See FEATURE.md for status."
exit 0
