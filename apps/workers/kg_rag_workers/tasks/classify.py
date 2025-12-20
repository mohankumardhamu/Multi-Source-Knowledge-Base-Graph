from __future__ import annotations

import uuid
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from libs.common.kg_rag_common.settings import get_settings
from libs.common.kg_rag_common.models import Document, Chunk, IngestionStatus
from libs.common.kg_rag_common.classify import classify_document, detect_topics


def _session() -> Session:
    s = get_settings()
    engine = create_engine(str(s.postgres_dsn), pool_pre_ping=True, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


@shared_task(name="classify.run")
def run(doc_id: str) -> None:
    session = _session()
    try:
        doc_uuid = uuid.UUID(doc_id)
        doc: Document | None = session.get(Document, doc_uuid)
        if not doc:
            return

        chunks = (
            session.query(Chunk).filter(Chunk.document_id == doc_uuid).all()
        )
        texts = [c.content for c in chunks]
        lang, _topics = classify_document(texts)

        # update domain only if not provided
        if doc.domain in (None, "", "unknown") and lang:
            doc.domain = lang
        session.add(doc)

        # per-chunk topics
        for c in chunks:
            # combine heading and content to infer topics
            heading = " ".join((c.heading_path or {}).get("path", [])) if isinstance(c.heading_path, dict) else ""
            topics = detect_topics(f"{heading}\n{c.content}")
            c.topics = topics
            session.add(c)

        # update ingestion status stage
        status_row = (
            session.query(IngestionStatus)
            .filter(IngestionStatus.document_id == doc_uuid)
            .one_or_none()
        )
        if status_row is not None:
            events = status_row.stages.get("events", [])
            events.append({"stage": "classified", "ts": datetime.now(timezone.utc).isoformat(), "status": "completed"})
            status_row.stages = {"events": events}
            session.add(status_row)

        session.commit()

        # chain next task
        from apps.workers.kg_rag_workers.worker import make_celery

        celery = make_celery()
        celery.send_task("embed.prepare", args=[doc_id])
    finally:
        session.close()

