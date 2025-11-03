from __future__ import annotations

from fastapi import APIRouter

from kg_rag_common.dto import HealthResponse
from kg_rag_common.settings import get_settings


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="api",
        environment=settings.environment,
    )

