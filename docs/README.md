# Service Ports and Endpoints

This document lists all the services in the Multi-Source Knowledge Base Graph project and the ports they are mapped to.

## Service Mapping Table

| Service | Port (Host) | Port (Container) | Description |
| :--- | :--- | :--- | :--- |
| **UI (Minimal)** | 3000 | 80 | Legacy/Minimalist Web UI |
| **API (FastAPI)** | 8000 | 8000 | Backend API service & Docs |
| **Postgres** | 5432 | 5432 | Primary Relational Database |
| **Redis** | 6379 | 6379 | Celery Broker & Caching |
| **Qdrant** | 6333 | 6333 | Vector Database (HTTP API) |
| **Qdrant (gRPC)** | 6334 | 6334 | Vector Database (gRPC) |
| **Neo4j (HTTP)** | 7474 | 7474 | Graph Database Management UI |
| **Neo4j (Bolt)** | 7687 | 7687 | Graph Database Bolt Protocol |
| **MinIO API** | 9000 | 9000 | Object Storage API (S3 compatible) |
| **MinIO Console** | 9001 | 9001 | MinIO Web Management Console |
| **pgAdmin** | 5050 | 80 | PostgreSQL Administration UI |
| **RedisInsight** | 5540 | 5540 | Redis GUI for monitoring |

## Accessing Services

- **Web UI**: [http://localhost:3000](http://localhost:3000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MinIO Console**: [http://localhost:9001](http://localhost:9001) (Credentials: `minioadmin` / `minioadmin`)
- **pgAdmin**: [http://localhost:5050](http://localhost:5050) (Credentials: `admin@example.com` / `admin`)
- **Neo4j UI**: [http://localhost:7474](http://localhost:7474) (Credentials: `neo4j` / `password`)
- **RedisInsight**: [http://localhost:5540](http://localhost:5540)
