# kg-rag

A mono-repo for a knowledge-graph RAG stack.

- apps/api: FastAPI service with health endpoints
- apps/workers: Celery workers on Redis
- libs/common: Shared DTOs and settings via pydantic-settings
- infra: Docker Compose stack for development (Postgres, Redis, Qdrant, Neo4j, MinIO, API, Workers)

## Requirements

- Python 3.11+
- Poetry
- Docker + Docker Compose

## Install Dependencies with uv (alternative)

If you prefer using uv for fast installs and isolated execution, you can install dependencies from this Poetry-based project without installing Poetry globally.

1) Install uv

- macOS (Homebrew): `brew install uv`
- Linux/macOS (curl): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows (PowerShell): `irm https://astral.sh/uv/install.ps1 | iex`

2) Create and activate a virtual environment

- Create: `uv venv`
- Activate: `source .venv/bin/activate` (Windows: `..\.venv\Scripts\activate`)

3) Install project dependencies (exported from Poetry)

- Runtime deps only:
  - `uvx --from poetry poetry export -f requirements.txt --without-hashes | uv pip install -r -`
- Include dev deps:
  - `uvx --from poetry poetry export -f requirements.txt --without-hashes --with dev | uv pip install -r -`

Notes:
- `uvx` runs Poetry ephemerally; no global Poetry install required for the export step.
- The Makefile targets currently use `poetry run`. If you’re using uv-only, you can invoke tools directly (e.g., `pytest`, `ruff`) inside the activated venv.

## Make Targets

- `make up` — Start the dev stack via docker-compose
- `make down` — Stop and remove the dev stack
- `make test` — Run unit tests with Poetry
- `make lint` — Run ruff, black, isort, and mypy

## Local Development

1. Install dependencies:
   - `poetry install`
2. Run tests:
   - `make test`
3. Start the stack:
   - `make up`
4. API available at:
   - http://localhost:8000

OpenAPI docs at http://localhost:8000/docs and http://localhost:8000/redoc
