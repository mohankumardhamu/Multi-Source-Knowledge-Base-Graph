#!/usr/bin/env sh
set -e

# Run DB migrations
alembic upgrade head

# Start API
exec uvicorn kg_rag_api.main:app --host 0.0.0.0 --port 8000

