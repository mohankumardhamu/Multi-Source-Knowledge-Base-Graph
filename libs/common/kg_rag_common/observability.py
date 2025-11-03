from __future__ import annotations

import logging
import os
import threading
import time
from typing import Callable

import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, start_http_server
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


# Prometheus metrics
HTTP_REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request duration seconds", ["method", "path"]
)
CELERY_QUEUE_DEPTH = Gauge("celery_queue_depth", "Celery queue depth", ["queue"]) 
CELERY_TASKS_STARTED = Counter("celery_tasks_started_total", "Celery tasks started", ["task"]) 
CELERY_TASKS_SUCCEEDED = Counter("celery_tasks_succeeded_total", "Celery tasks succeeded", ["task"]) 
CELERY_TASKS_FAILED = Counter("celery_tasks_failed_total", "Celery tasks failed", ["task"]) 
CELERY_TASK_LATENCY = Histogram("celery_task_duration_seconds", "Celery task duration seconds", ["task"]) 


def configure_logging(service_name: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    structlog.get_logger().info("logging_configured", service=service_name)


def configure_tracing(service_name: str) -> None:
    ratio = float(os.getenv("OTEL_TRACES_SAMPLER_ARG", os.getenv("KG_OTEL_SAMPLER_RATIO", "0.1")))
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource, sampler=TraceIdRatioBased(ratio))
    if endpoint:
        exporter = OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces")
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Auto-instrument libraries used by API/workers
    RequestsInstrumentor().instrument()
    RedisInstrumentor().instrument()
    try:
        SQLAlchemyInstrumentor().instrument()
    except Exception:
        pass


def configure_metrics_api(app) -> None:
    # Instrument FastAPI
    try:
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        pass

    @app.middleware("http")
    async def _metrics_middleware(request, call_next):
        method = request.method
        path = request.url.path
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        HTTP_REQUESTS.labels(method=method, path=path, status=str(response.status_code)).inc()
        HTTP_LATENCY.labels(method=method, path=path).observe(duration)
        return response

    from fastapi import Response

    @app.get("/metrics")
    def _metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def start_worker_metrics_server(port: int = 9109) -> None:
    # start a Prometheus HTTP server in a background thread
    start_http_server(port)


def start_queue_depth_probe(redis_url: str, queue_name: str = "celery", interval: float = 5.0) -> None:
    import redis

    r = redis.from_url(redis_url)

    def _loop():
        while True:
            try:
                depth = r.llen(queue_name) or 0
                CELERY_QUEUE_DEPTH.labels(queue=queue_name).set(depth)
            except Exception:
                pass
            time.sleep(interval)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
