# Docker Deployment Summary

## What Was Added

### 1. Frontend Dockerfile
**Location:** `frontend/Dockerfile`

Multi-stage build for optimal production deployment:
- **Stage 1 (Builder)**: Node.js 18 Alpine
  - Installs dependencies with `npm ci`
  - Builds the React app with `npm run build`
  - Output: Production-ready static files in `dist/`

- **Stage 2 (Production)**: Nginx Alpine
  - Copies built assets from builder stage
  - Serves static files
  - Lightweight final image (~50MB)

### 2. Nginx Configuration
**Location:** `frontend/nginx.conf`

Features:
- Serves React app from `/usr/share/nginx/html`
- SPA routing (all routes fallback to `index.html`)
- API proxying to backend:
  - `/v1/*` → `http://api:8000`
  - `/admin/*` → `http://api:8000`
  - `/health` → `http://api:8000`
- Gzip compression enabled
- Cache headers for static assets (1 year)

### 3. Docker Compose Service
**Location:** `infra/docker-compose.yml`

Added new `frontend` service:
```yaml
frontend:
  build:
    context: ..
    dockerfile: frontend/Dockerfile
  depends_on:
    - api
  ports:
    - "3001:80"
  environment:
    - NODE_ENV=production
```

### 4. Supporting Files
- `.dockerignore` - Excludes node_modules, dist, etc. from build context
- `.env.example` - Template for environment variables

### 5. Documentation Updates
- `frontend/README.md` - Added Docker deployment section
- Main `README.md` - Updated to mention both UIs
- `frontend/WALKTHROUGH.md` - Comprehensive Docker guide

## How to Use

### Start Everything with Docker

From the project root:

```bash
make up
```

This starts:
- All backend services (Postgres, Redis, Qdrant, Neo4j, MinIO, API, Workers)
- Original minimal UI on port 3000
- **New React frontend on port 3001**

### Access Points

- **New Frontend**: http://localhost:3001
- **Old UI**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Rebuild Frontend Only

If you make changes to the frontend:

```bash
cd infra
docker-compose build frontend
docker-compose up -d frontend
```

### View Logs

```bash
docker-compose -f infra/docker-compose.yml logs frontend
```

### Stop Everything

```bash
make down
```

## Architecture

```
┌─────────────────────────────────────────────┐
│  Browser (http://localhost:3001)            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Frontend Container (Nginx)                 │
│  - Serves React static files                │
│  - Port 3001:80                             │
└──────────────────┬──────────────────────────┘
                   │
                   │ Proxies /v1/*, /admin/*
                   ▼
┌─────────────────────────────────────────────┐
│  API Container (FastAPI)                    │
│  - Port 8000:8000                           │
│  - Connects to: Postgres, Redis, Qdrant,   │
│    Neo4j, MinIO                             │
└─────────────────────────────────────────────┘
```

## Benefits

1. **Production-Ready**: Optimized build with Nginx serving
2. **Isolated**: Frontend runs in its own container
3. **Scalable**: Easy to add load balancing or multiple instances
4. **Consistent**: Same environment for dev and production
5. **Fast**: Static assets cached, gzip compression enabled
6. **Simple**: Single `make up` command starts everything

## Next Steps

1. Test the Docker deployment:
   ```bash
   make up
   open http://localhost:3001
   ```

2. Upload a document and test all features

3. For production:
   - Add SSL/TLS termination
   - Configure domain names
   - Set up monitoring
   - Add health checks
