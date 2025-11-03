# Ensure tasks are registered when this package is imported by Celery
from .ingest import process  # noqa: F401
from .classify import run as classify_run  # noqa: F401
