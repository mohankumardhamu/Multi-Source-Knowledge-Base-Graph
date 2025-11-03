from __future__ import annotations

import os

from celery import Celery

from kg_rag_common.settings import get_settings
from kg_rag_common.observability import (
    configure_logging,
    configure_tracing,
    start_worker_metrics_server,
    start_queue_depth_probe,
    CELERY_TASKS_STARTED,
    CELERY_TASKS_SUCCEEDED,
    CELERY_TASKS_FAILED,
    CELERY_TASK_LATENCY,
)
from prometheus_client import Summary
from celery.signals import task_prerun, task_postrun, task_failure
import time


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

# Observability setup for workers
configure_logging("kg-rag-worker")
configure_tracing("kg-rag-worker")
start_worker_metrics_server(int(os.getenv("METRICS_PORT", "9109")))
start_queue_depth_probe(str(get_settings().redis_dsn))

_task_start_times: dict[str, float] = {}


@task_prerun.connect
def _on_task_prerun(sender=None, task_id=None, task=None, **kwargs):
    name = getattr(task, "name", str(task))
    CELERY_TASKS_STARTED.labels(task=name).inc()
    _task_start_times[task_id] = time.perf_counter()


@task_postrun.connect
def _on_task_postrun(sender=None, task_id=None, task=None, **kwargs):
    name = getattr(task, "name", str(task))
    CELERY_TASKS_SUCCEEDED.labels(task=name).inc()
    start = _task_start_times.pop(task_id, None)
    if start is not None:
        CELERY_TASK_LATENCY.labels(task=name).observe(time.perf_counter() - start)


@task_failure.connect
def _on_task_failure(sender=None, task_id=None, task=None, **kwargs):
    name = getattr(task, "name", str(task))
    CELERY_TASKS_FAILED.labels(task=name).inc()

if __name__ == "__main__":
    # For local debugging: `python -m kg_rag_workers.worker`
    celery_app.start(argv=[
        "celery",
        "-A",
        "kg_rag_workers.worker:celery_app",
        "worker",
        "--loglevel=INFO",
    ])
