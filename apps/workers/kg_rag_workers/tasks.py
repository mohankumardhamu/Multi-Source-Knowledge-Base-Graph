from __future__ import annotations

from celery import shared_task


@shared_task(name="kg_rag.ping")
def ping() -> str:
    return "pong"

