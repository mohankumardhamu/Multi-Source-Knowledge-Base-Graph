from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from kg_rag_api.routes.health import router as health_router
from kg_rag_api.routes.docs import router as docs_router
from kg_rag_api.routes.search import router as search_router
from kg_rag_api.routes.generate import router as generate_router
from kg_rag_api.routes.roadmap import router as roadmap_router
from kg_rag_common.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: could initialize DB connections, clients, etc.
    yield
    # Shutdown: cleanup


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="kg-rag API",
        version="0.1.0",
        description="FastAPI service for the kg-rag stack.",
        lifespan=lifespan,
    )

    app.include_router(health_router)
    app.include_router(docs_router)
    app.include_router(search_router)
    app.include_router(generate_router)
    app.include_router(roadmap_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"app": settings.app_name, "status": "ok"}

    return app


app = create_app()
