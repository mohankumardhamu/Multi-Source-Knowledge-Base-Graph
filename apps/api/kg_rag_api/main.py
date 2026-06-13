from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI

from apps.api.kg_rag_api.auth import verify_token
from apps.api.kg_rag_api.routes.health import router as health_router
from apps.api.kg_rag_api.routes.docs import router as docs_router
from apps.api.kg_rag_api.routes.search import router as search_router
from apps.api.kg_rag_api.routes.generate import router as generate_router
from apps.api.kg_rag_api.routes.roadmap import router as roadmap_router
from apps.api.kg_rag_api.routes.answer import router as answer_router
from apps.api.kg_rag_api.routes.agent import router as agent_router
from apps.api.kg_rag_api.routes.ui import router as ui_router
from apps.api.kg_rag_api.routes.admin_api import router as admin_api_router
from libs.common.kg_rag_common.settings import get_settings
from libs.common.kg_rag_common.observability import configure_logging, configure_tracing, configure_metrics_api


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: could initialize DB connections, clients, etc.
    yield
    # Shutdown: cleanup


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging("kg-rag-api")
    configure_tracing("kg-rag-api")
    app = FastAPI(
        title="kg-rag API",
        version="0.1.0",
        description="FastAPI service for the kg-rag stack.",
        lifespan=lifespan,
    )

    app.include_router(health_router)
    app.include_router(docs_router, dependencies=[Depends(verify_token)])
    app.include_router(search_router, dependencies=[Depends(verify_token)])
    app.include_router(generate_router, dependencies=[Depends(verify_token)])
    app.include_router(roadmap_router, dependencies=[Depends(verify_token)])
    app.include_router(answer_router, dependencies=[Depends(verify_token)])
    app.include_router(agent_router, dependencies=[Depends(verify_token)])
    app.include_router(ui_router)
    app.include_router(admin_api_router, dependencies=[Depends(verify_token)])

    configure_metrics_api(app)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"app": settings.app_name, "status": "ok"}

    return app


app = create_app()
