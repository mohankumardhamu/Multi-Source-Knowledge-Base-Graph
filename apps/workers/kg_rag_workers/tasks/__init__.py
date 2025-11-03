# Ensure tasks are registered when this package is imported by Celery
from .ingest import process  # noqa: F401
from .classify import run as classify_run  # noqa: F401
from .embed import prepare as embed_prepare  # noqa: F401
from .graph import build as graph_build  # noqa: F401
