from __future__ import annotations

import os

from celery import Celery

from kg_rag_common.settings import get_settings


def make_celery() -> Celery:
    settings = get_settings()
    broker_url = str(settings.redis_dsn)
    backend_url = str(settings.redis_dsn)

    app = Celery(
        "kg_rag",
        broker=broker_url,
        backend=backend_url,
        include=["kg_rag_workers.tasks"],
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        worker_send_task_events=True,
        task_send_sent_event=True,
    )
    return app


celery_app = make_celery()

if __name__ == "__main__":
    # For local debugging: `python -m kg_rag_workers.worker`
    celery_app.start(argv=[
        "celery",
        "-A",
        "kg_rag_workers.worker:celery_app",
        "worker",
        "--loglevel=INFO",
    ])
