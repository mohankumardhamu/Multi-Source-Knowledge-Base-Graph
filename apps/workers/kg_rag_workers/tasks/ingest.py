from __future__ import annotations

import json
from datetime import datetime, timezone
import uuid

from celery import shared_task
from sqlalchemy import update
from sqlalchemy.orm import Session

from libs.common.kg_rag_common.models import IngestionStatus, Document, Chunk
from libs.common.kg_rag_common.settings import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import boto3
from botocore.exceptions import ClientError
from libs.common.kg_rag_common.text_extraction import extract_pdf_blocks


def _session() -> Session:
    settings = get_settings()
    engine = create_engine(str(settings.postgres_dsn), pool_pre_ping=True, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


def _s3_client():
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint_url,
        aws_access_key_id=s.s3_access_key,
        aws_secret_access_key=s.s3_secret_key,
    )


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
        # Download PDF from object storage
        doc_row: Document | None = session.get(Document, doc_uuid)
        if not doc_row:
            raise RuntimeError("Document not found")
        s3 = _s3_client()
        obj = s3.get_object(Bucket=doc_row.s3_bucket, Key=doc_row.s3_key)
        pdf_bytes: bytes = obj["Body"].read()

        # Extract blocks
        blocks = extract_pdf_blocks(pdf_bytes)

        # Persist chunks
        for b in blocks:
            chunk = Chunk(
                document_id=doc_uuid,
                page_from=b.page_from,
                page_to=b.page_to,
                heading_path={"path": b.heading_path},
                block_type=b.block_type,
                token_count=b.token_count,
                content=b.content,
            )
            session.add(chunk)
        session.commit()

        # mark finished
        now2 = datetime.now(timezone.utc).isoformat()
        if status_row is not None:
            events = status_row.stages.get("events", [])
            events.append({"stage": "extracted", "ts": now2, "status": "completed"})
            status_row.status = "completed"
            status_row.stages = {"events": events}
        session.execute(
            update(Document).where(Document.id == doc_uuid).values(status="completed")
        )
        session.commit()

        # Emit next task in pipeline (classification)
        from apps.workers.kg_rag_workers.worker import make_celery

        celery = make_celery()
        celery.send_task("classify.run", args=[doc_id])
    finally:
        session.close()
