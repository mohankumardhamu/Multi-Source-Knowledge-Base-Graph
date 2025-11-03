from __future__ import annotations

import math
import re
import uuid
from typing import Iterable, List, Tuple

from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from kg_rag_common.settings import get_settings
from kg_rag_common.models import Document, Chunk
from kg_rag_common.embeddings import get_provider
from kg_rag_common.qdrant_util import get_client, ensure_collection, upsert_vectors


def _session() -> Session:
    s = get_settings()
    engine = create_engine(str(s.postgres_dsn), pool_pre_ping=True, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


def _tokenize(text: str) -> List[str]:
    return (text or "").split()


def rechunk_text_windows(chunks: List[Chunk], window_tokens: int = 800, overlap: float = 0.1) -> List[Tuple[str, int, int, List[str], List[str]]]:
    """Return list of (content, page_from, page_to, heading_path, topics).
    Concatenate text chunks by order and produce sliding windows.
    """
    pieces: List[Tuple[str, int, int, List[str], List[str]]] = []
    texts: List[str] = []
    pages: List[Tuple[int, int]] = []
    headings: List[List[str]] = []
    topics_list: List[List[str]] = []
    for c in chunks:
        texts.append(c.content)
        pages.append((c.page_from, c.page_to))
        h = c.heading_path.get("path", []) if isinstance(c.heading_path, dict) else []
        headings.append(h)
        topics_list.append(c.topics if isinstance(c.topics, list) else [])
    full_text = "\n\n".join(texts)
    tokens = _tokenize(full_text)
    if not tokens:
        return pieces
    step = max(1, int(window_tokens * (1 - overlap)))
    for start in range(0, len(tokens), step):
        window = tokens[start : start + window_tokens]
        if not window:
            break
        content = " ".join(window)
        # approximate pages as min/max of all included
        page_from = min(p[0] for p in pages)
        page_to = max(p[1] for p in pages)
        # combine headings and topics
        heading_path = list(dict.fromkeys([x for h in headings for x in h]))
        uniq_topics = list(dict.fromkeys([t for ts in topics_list for t in ts]))
        pieces.append((content, page_from, page_to, heading_path, uniq_topics))
        if start + window_tokens >= len(tokens):
            break
    return pieces


_PY_FUNC_RE = re.compile(r"^\s*def\s+\w+\(.*\):", re.M)
_JAVA_FUNC_RE = re.compile(r"^\s*(public|private|protected)?\s*(static\s+)?[\w<>\[\]]+\s+\w+\(.*\)\s*\{", re.M)


def split_code_functions(block: Chunk, lang: str | None) -> List[str]:
    text = block.content or ""
    if lang == "python":
        parts = _PY_FUNC_RE.split(text)
        # _PY_FUNC_RE splits off the signature; keep simple lines split by two newlines if no match
        return [p.strip() for p in parts if p.strip()] if len(parts) > 1 else [t.strip() for t in text.split("\n\n") if t.strip()]
    if lang == "java":
        parts = _JAVA_FUNC_RE.split(text)
        return [p.strip() for p in parts if p.strip()] if len(parts) > 1 else [t.strip() for t in text.split("\n\n") if t.strip()]
    return [text] if text.strip() else []


@shared_task(name="embed.prepare")
def prepare(doc_id: str) -> None:
    session = _session()
    try:
        doc = session.get(Document, uuid.UUID(doc_id))
        if not doc:
            return
        domain = (doc.domain or "default").lower()
        collection = f"vectors_{domain}"

        # Load chunks for this document
        rows: List[Chunk] = (
            session.query(Chunk).filter(Chunk.document_id == doc.id).all()
        )
        text_chunks = [c for c in rows if c.block_type == "text"]
        code_chunks = [c for c in rows if c.block_type == "code"]

        # Build windows for text
        text_windows = rechunk_text_windows(text_chunks)

        # Split code by functions (best-effort)
        code_snippets: List[Tuple[str, int, int, List[str], List[str]]] = []
        for c in code_chunks:
            for snippet in split_code_functions(c, domain):
                if not snippet:
                    continue
                h = c.heading_path.get("path", []) if isinstance(c.heading_path, dict) else []
                code_snippets.append((snippet, c.page_from, c.page_to, h, c.topics if isinstance(c.topics, list) else []))

        provider = get_provider()
        client = get_client()
        ensure_collection(client, collection, provider.dimension)

        # Prepare points
        points: List[Tuple[str, list[float], dict]] = []
        all_items = [("text", *tw) for tw in text_windows] + [("code", *cs) for cs in code_snippets]
        if not all_items:
            return
        texts = [i[1] for i in all_items]
        vectors = provider.embed_texts(texts)
        for (block_type, content, page_from, page_to, heading_path, topics), vec in zip(all_items, vectors):
            pid = str(uuid.uuid4())
            payload = {
                "doc_id": str(doc.id),
                "chunk_id": pid,
                "domain": domain,
                "topics": topics,
                "page_from": page_from,
                "page_to": page_to,
                "heading_path": heading_path,
                "block_type": block_type,
                # include snippet to support downstream generation without DB
                "content": (content or "")[:1000],
            }
            points.append((pid, vec, payload))

        upsert_vectors(client, collection, points)
    finally:
        session.close()
