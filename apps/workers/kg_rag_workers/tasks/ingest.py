from __future__ import annotations

import json
from datetime import datetime, timezone
import uuid

from celery import shared_task
from sqlalchemy import update
from sqlalchemy.orm import Session

from kg_rag_common.models import IngestionStatus, Document
from kg_rag_common.settings import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _session() -> Session:
    settings = get_settings()
    engine = create_engine(str(settings.postgres_dsn), pool_pre_ping=True, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


@shared_task(name="ingest.process")
def process(doc_id: str) -> None:
    """Stub ingestion task: updates status and appends simple stage events.

    Replace with real ingestion pipeline steps as needed.
    """
    session = _session()
    try:
        # mark processing
        now = datetime.now(timezone.utc).isoformat()
        doc_uuid = uuid.UUID(doc_id)
        status_row = (
            session.query(IngestionStatus)
            .filter(IngestionStatus.document_id == doc_uuid)
            .one_or_none()
        )

        # Fallback: update by id via SQL to avoid UUID conversion issues in stub
        if status_row is None:
            session.execute(
                update(Document).where(Document.id == doc_uuid).values(status="processing")
            )
        else:
            events = status_row.stages.get("events", [])
            events.append({"stage": "start", "ts": now, "status": "processing"})
            status_row.status = "processing"
            status_row.stages = {"events": events}

        session.commit()

        # simulate finish
        now2 = datetime.now(timezone.utc).isoformat()
        if status_row is not None:
            events = status_row.stages.get("events", [])
            events.append({"stage": "finish", "ts": now2, "status": "completed"})
            status_row.status = "completed"
            status_row.stages = {"events": events}
        session.execute(
            update(Document).where(Document.id == doc_uuid).values(status="completed")
        )
        session.commit()
    finally:
        session.close()
