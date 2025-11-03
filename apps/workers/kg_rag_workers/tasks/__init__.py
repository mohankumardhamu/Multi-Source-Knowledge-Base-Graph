# Ensure tasks are registered when this package is imported by Celery
from .ingest import process  # noqa: F401

