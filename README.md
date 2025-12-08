# kg-rag

A mono-repo for a knowledge-graph RAG stack.

- apps/api: FastAPI service with health endpoints
- apps/workers: Celery workers on Redis
- libs/common: Shared DTOs and settings via pydantic-settings
- infra: Docker Compose stack for development (Postgres, Redis, Qdrant, Neo4j, MinIO, API, Workers)
 - ui: Minimal React single‑page app (served by Nginx) proxying to the API

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

## Getting Started (curl)

- Upload a PDF (multipart):

```bash
curl -sS -X POST http://localhost:8000/v1/docs \
  -F file=@/path/to/file.pdf \
  -F title="My Sample Doc" \
  -F domain="python"
```

Response includes an `id`. Check status:

```bash
curl -sS http://localhost:8000/v1/docs/<DOCUMENT_ID>/status | jq .
```

- Vector search (by domain):

```bash
curl -sS -X POST http://localhost:8000/v1/search/vector \
  -H 'Content-Type: application/json' \
  -d '{
        "query": "how do http servers handle requests?",
        "domain": "python",
        "top_k": 5
      }' | jq .
```

- Get an answer with citations (domain optional; auto-classified if omitted):

```bash
curl -sS -X POST http://localhost:8000/v1/answer \
  -H 'Content-Type: application/json' \
  -d '{
        "query": "Explain concurrency in Python and common pitfalls.",
        "domain": "python",
        "top_k": 5
      }' | jq .
```

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

- UI (React over Nginx)
  - URL: http://localhost:3000
  - Routes:
    - /admin — document list with re‑run buttons (calls API)
    - /explore/graph — runs canned Cypher via /v1/search/graph
    - /learn/roadmap?domain=python — renders roadmap JSON by week
  - Note: This is the minimal original UI

- Frontend (Modern React App)
  - URL: http://localhost:3001
  - Features:
    - Document upload and management
    - Vector and graph search
    - Q&A assistant with citations
    - Learning roadmap visualization
    - Admin dashboard with system metrics
  - Built with: React 18, TypeScript, shadcn/ui, Tailwind CSS
  - See `frontend/README.md` for details

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

## Observability

- Logging (structlog JSON)
  - API and workers emit structured JSON logs to stdout.
  - Configured via `kg_rag_common.observability.configure_logging`.

- Metrics (Prometheus)
  - API endpoint: `GET /metrics` (default on http://localhost:8000/metrics)
  - Workers expose a Prometheus HTTP server (default `9109` inside container). Publish a port if you want to scrape from host.
  - Included metrics:
    - http_requests_total{method,path,status}
    - http_request_duration_seconds{method,path}
    - celery_queue_depth{queue}
    - celery_tasks_started_total{task}, celery_tasks_succeeded_total{task}, celery_tasks_failed_total{task}
    - celery_task_duration_seconds{task}

- Tracing (OpenTelemetry)
  - Auto‑instrumented libs: FastAPI, SQLAlchemy, Redis, Requests
  - Configure OTLP exporter endpoint via env: `OTEL_EXPORTER_OTLP_ENDPOINT` (e.g. `http://otel-collector:4318`)
  - Sampling: set ratio via `KG_OTEL_SAMPLER_RATIO` (default 0.1) or `OTEL_TRACES_SAMPLER_ARG`

## Admin and Ops APIs

- Documents + metrics overview
  - `GET /v1/admin/overview` → JSON with:
    - `documents`: uploaded docs from Postgres
    - `qdrant`: collections and total points
    - `neo4j`: node and relationship counts
    - `redis`: keys count
    - `postgres`: per‑table row counts

## Core API Endpoints (selection)

- Ingestion
  - `POST /v1/docs` — upload a PDF (multipart: file, title, optional domain)
  - `GET /v1/docs/{id}/status` — ingestion status + stages

- Search
  - `POST /v1/search/vector` — vector similarity; supports `filters`
  - `POST /v1/search/graph` — read‑only Cypher execution

- Generation and Q&A
  - `POST /v1/generate/questions` — deterministic templated questions
    - Response includes `status` field: `vector` or `fallback`
  - `GET /v1/questions/{id}` — fetch a stored question
  - `POST /v1/generate/roadmap` — build study roadmap nodes/edges
  - `GET /v1/roadmaps/{domain}` — fetch roadmap JSON
  - `POST /v1/answer` — compose an answer with citations and next topics

- Agent
  - `POST /v1/agent/ask` — modes: `qa`, `tutor`, `interview`

## Data Flow (high‑level)

1) Upload PDF → stored in MinIO, `documents` row created
2) Celery pipeline: `ingest.process` → `classify.run` → `embed.prepare` → `graph.build`
   - Extract chunks (text/code), topics, and store in Postgres
   - Embed chunks, upsert vectors into Qdrant (collection per domain)
   - Build Neo4j nodes: Domain, Document, Chunk, Topic, relations

## Configuration (env)

- API
  - `KG_POSTGRES_DSN` (e.g., `postgresql+psycopg://kg:kg_pass@postgres:5432/kgdb`)
  - `KG_REDIS_DSN` (e.g., `redis://redis:6379/0`)
  - `KG_QDRANT_URL` (e.g., `http://qdrant:6333`)
  - `KG_S3_*` — MinIO/S3 endpoint and credentials
  - OpenTelemetry: `OTEL_EXPORTER_OTLP_ENDPOINT`, `KG_OTEL_SAMPLER_RATIO`

- Workers
  - Same `KG_*` vars as API
  - `METRICS_PORT` for Prometheus worker metrics (default `9109`)

- UI
  - Served at http://localhost:3000 and proxies API paths to `api:8000` inside Docker.
