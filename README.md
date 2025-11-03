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

## Dev Stack Access

Start the stack:

- `make up` (or `docker compose -f infra/docker-compose.yml up -d`)

Services and how to access them:

- API (FastAPI)
  - Base: http://localhost:8000
  - Health: http://localhost:8000/health
  - OpenAPI: http://localhost:8000/docs and http://localhost:8000/redoc
  - Upload docs: `POST /v1/docs` (multipart form fields: `file`, `title`, optional `domain`)

- Postgres
  - Host: `localhost`, Port: `5432`
  - User: `kg`, Password: `kg_pass`, DB: `kgdb`
  - DSN: `postgresql://kg:kg_pass@localhost:5432/kgdb`
  - Viewers: pgAdmin, DBeaver, TablePlus (use the above connection details)

- Redis
  - Host: `localhost`, Port: `6379` (no password)
  - CLI: `redis-cli -h localhost -p 6379`
  - GUI: RedisInsight or similar

- Qdrant (Vector DB)
  - REST: http://localhost:6333
  - gRPC: `localhost:6334`
  - Quick check: `curl http://localhost:6333/collections`
  - UI: not included; use API/clients or add a dashboard container if needed

- Neo4j
  - Browser UI: http://localhost:7474
  - Bolt endpoint: `bolt://localhost:7687`
  - Credentials: `neo4j` / `password`

- MinIO (Object Storage)
  - Console (web UI): http://localhost:9001
  - S3 API endpoint: http://localhost:9000
  - Access key: `minioadmin`, Secret key: `minioadmin`

- Workers (Celery)
  - No exposed ports; processes background jobs via Redis

- pgAdmin (Postgres UI)
  - URL: http://localhost:5050
  - Login: `admin@example.com` / `admin` (override with env vars `PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD`)
  - Add server inside pgAdmin:
    - Host: `postgres`, Port: `5432`, Username: `kg`, Password: `kg_pass`, DB: `kgdb`
    - Note: When using a desktop client outside Docker, use host `localhost` instead of `postgres`.

- RedisInsight (Redis UI)
  - URL: http://localhost:5540
  - Add database connection:
    - Host: `redis`, Port: `6379` (no password)
    - Note: From outside Docker, connect to `localhost:6379`.
