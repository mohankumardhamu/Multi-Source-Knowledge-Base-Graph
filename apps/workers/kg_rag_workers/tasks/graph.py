from __future__ import annotations

import uuid

from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from libs.common.kg_rag_common.settings import get_settings
from libs.common.kg_rag_common.models import Document, Chunk
from libs.common.kg_rag_common import graph as g


def _session() -> Session:
    s = get_settings()
    engine = create_engine(str(s.postgres_dsn), pool_pre_ping=True, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


@shared_task(name="graph.build")
def build(doc_id: str) -> None:
    session = _session()
    try:
        doc = session.get(Document, uuid.UUID(doc_id))
        if not doc:
            return
        domain = (doc.domain or "default").lower()

        chunks = session.query(Chunk).filter(Chunk.document_id == doc.id).all()

        driver = g.get_driver()
        with g.session_ctx(driver) as neo:
            # Domain and Document
            def write_domain(tx):
                g.upsert_domain_tx(tx, domain)

            def write_doc(tx):
                g.upsert_document_tx(
                    tx,
                    {
                        "id": str(doc.id),
                        "title": doc.title,
                        "checksum_sha256": doc.checksum_sha256,
                        "s3_bucket": doc.s3_bucket,
                        "s3_key": doc.s3_key,
                    },
                )
                g.link_document_domain_tx(tx, str(doc.id), domain)

            g.execute_write(neo, write_domain)
            g.execute_write(neo, write_doc)

            # Chunks and Topics
            for c in chunks:
                def write_chunk(tx, c=c):
                    g.upsert_chunk_tx(
                        tx,
                        str(doc.id),
                        {
                            "id": str(c.id) if getattr(c, "id", None) else str(uuid.uuid4()),
                            "page_from": c.page_from,
                            "page_to": c.page_to,
                            "block_type": c.block_type,
                            "heading_path": c.heading_path,
                        },
                    )
                    g.upsert_topics_tx(tx, domain, str(c.id), list(c.topics or []))

                g.execute_write(neo, write_chunk)
    finally:
        session.close()

