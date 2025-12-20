from __future__ import annotations

import uuid
from typing import Any

import pytest

from libs.common.kg_rag_common.embeddings import EmbeddingProvider


class FixedProvider(EmbeddingProvider):
    def __init__(self, dim: int = 8):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts):
        return [[1.0] * self._dim for _ in texts]


class FakeDoc:
    def __init__(self, domain: str = "python"):
        self.id = uuid.uuid4()
        self.domain = domain


class FakeChunk:
    def __init__(self, doc_id, content, block_type="text", page_from=1, page_to=1, heading_path=None, topics=None):
        self.id = uuid.uuid4()
        self.document_id = doc_id
        self.content = content
        self.block_type = block_type
        self.page_from = page_from
        self.page_to = page_to
        self.heading_path = heading_path or {"path": ["H1"]}
        self.topics = topics or []


class FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return self._rows


class FakeSession:
    def __init__(self, doc, chunks):
        self._doc = doc
        self._chunks = chunks

    def get(self, model, key):
        return self._doc

    def query(self, model):
        return FakeQuery(self._chunks)

    def close(self):
        pass


class CaptureQdrant:
    def __init__(self):
        self.created = []
        self.upserts = []

    def get_collections(self):
        class C:
            def __init__(self):
                self.collections = []

        return C()

    def create_collection(self, collection_name, vectors_config):
        self.created.append((collection_name, vectors_config))

    def upsert(self, collection_name, points):
        self.upserts.append((collection_name, points))


def test_embed_prepare_chunks_and_upserts(monkeypatch):
    from apps.workers.kg_rag_workers.tasks import embed as embed_task
    from libs.common.kg_rag_common import qdrant_util

    doc = FakeDoc(domain="python")
    # Create one long text content ~ 1000 tokens and a code block with two functions
    long_text = "word " * 1000
    code_text = "def a():\n    pass\n\ndef b():\n    pass\n"
    chunks = [
        FakeChunk(doc.id, long_text, block_type="text", page_from=1, page_to=2),
        FakeChunk(doc.id, code_text, block_type="code", page_from=3, page_to=3),
    ]

    # Monkeypatch session and provider
    monkeypatch.setattr(embed_task, "_session", lambda: FakeSession(doc, chunks))
    monkeypatch.setattr(
        embed_task, "get_provider", lambda: FixedProvider(dim=8)
    )

    # Capture Qdrant calls
    cap = CaptureQdrant()
    monkeypatch.setattr(qdrant_util, "get_client", lambda: cap)

    # Run
    embed_task.prepare(str(doc.id))

    # Should create collection vectors_python
    assert any(name == "vectors_python" for name, _ in cap.created)
    # Should upsert at least 2 points (text windows + 2 code functions)
    assert len(cap.upserts) >= 1
    total_points = sum(len(points) for _, points in cap.upserts)
    assert total_points >= 3

