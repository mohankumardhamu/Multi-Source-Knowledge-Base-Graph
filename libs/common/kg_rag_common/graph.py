from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from neo4j import GraphDatabase, basic_auth

from libs.common.kg_rag_common.settings import get_settings


def get_driver():
    s = get_settings()
    return GraphDatabase.driver(s.neo4j_url, auth=basic_auth(s.neo4j_user, s.neo4j_password))


@contextmanager
def session_ctx(driver):
    session = driver.session()
    try:
        yield session
    finally:
        session.close()


def execute_write(session, func: Callable):
    return session.execute_write(func)


def upsert_domain_tx(tx, domain: str) -> None:
    tx.run(
        """
        MERGE (d:Domain {name: $name})
        """,
        name=domain,
    )


def upsert_document_tx(tx, doc: dict[str, Any]) -> None:
    tx.run(
        """
        MERGE (doc:Document {id: $id})
        SET doc.title = $title,
            doc.checksum_sha256 = $checksum_sha256,
            doc.s3_bucket = $s3_bucket,
            doc.s3_key = $s3_key
        """,
        **doc,
    )


def link_document_domain_tx(tx, doc_id: str, domain: str) -> None:
    tx.run(
        """
        MATCH (doc:Document {id: $doc_id})
        MERGE (d:Domain {name: $domain})
        MERGE (doc)-[:BELONGS_TO]->(d)
        """,
        doc_id=doc_id,
        domain=domain,
    )


def upsert_chunk_tx(tx, doc_id: str, chunk: dict[str, Any]) -> None:
    tx.run(
        """
        MERGE (c:Chunk {id: $id})
        SET c.page_from = $page_from,
            c.page_to = $page_to,
            c.block_type = $block_type,
            c.heading_path = $heading_path
        WITH c
        MATCH (doc:Document {id: $doc_id})
        MERGE (c)-[:PART_OF]->(doc)
        """,
        doc_id=doc_id,
        **chunk,
    )


def upsert_topics_tx(tx, domain: str, chunk_id: str, topics: list[str]) -> None:
    tx.run(
        """
        MATCH (c:Chunk {id: $chunk_id})
        UNWIND $topics AS tname
        MERGE (t:Topic {name: tname})
        MERGE (c)-[:COVERS]->(t)
        MERGE (d:Domain {name: $domain})
        MERGE (t)-[:REFINES]->(d)
        """,
        chunk_id=chunk_id,
        topics=topics,
        domain=domain,
    )

