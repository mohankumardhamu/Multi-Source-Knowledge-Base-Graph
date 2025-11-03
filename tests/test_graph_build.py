from __future__ import annotations

import uuid


class FakeDoc:
    def __init__(self, domain: str = "python"):
        self.id = uuid.uuid4()
        self.domain = domain
        self.title = "T"
        self.checksum_sha256 = "abc"
        self.s3_bucket = "docs"
        self.s3_key = f"documents/{self.id}.pdf"


class FakeChunk:
    def __init__(self, doc_id, page_from=1, page_to=1, block_type="text", heading_path=None, topics=None):
        self.id = uuid.uuid4()
        self.document_id = doc_id
        self.page_from = page_from
        self.page_to = page_to
        self.block_type = block_type
        self.heading_path = heading_path or {"path": ["H1"]}
        self.topics = topics or ["networking"]


class FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *_a, **_k):
        return self

    def all(self):
        return self._rows


class FakeSessionDB:
    def __init__(self, doc, chunks):
        self._doc = doc
        self._chunks = chunks

    def get(self, model, key):
        return self._doc

    def query(self, model):
        return FakeQuery(self._chunks)

    def close(self):
        pass


class FakeTx:
    def __init__(self, calls):
        self.calls = calls

    def run(self, cypher, **params):
        self.calls.append((cypher.strip(), params))
        class R:
            def consume(self):
                return None
        return R()


class FakeNeo4jSession:
    def __init__(self, calls):
        self.calls = calls

    def execute_write(self, func):
        tx = FakeTx(self.calls)
        func(tx)

    def close(self):
        pass


class FakeDriver:
    def __init__(self, calls):
        self.calls = calls

    def session(self):
        return FakeNeo4jSession(self.calls)


def test_graph_build_merges_nodes_and_relationships(monkeypatch):
    from apps.workers.kg_rag_workers.tasks import graph as graph_task
    from kg_rag_common import graph as graph_util

    doc = FakeDoc(domain="python")
    chunks = [FakeChunk(doc.id), FakeChunk(doc.id, block_type="code", topics=["algorithms"])]

    # monkeypatch DB session
    monkeypatch.setattr(graph_task, "_session", lambda: FakeSessionDB(doc, chunks))

    # capture cypher calls
    calls = []
    monkeypatch.setattr(graph_util, "get_driver", lambda: FakeDriver(calls))

    # run task
    graph_task.build(str(doc.id))

    # assertions: we should MERGE Domain, Document, Chunk, Topic and relationships
    cyphers = "\n".join(c for c, _ in calls)
    assert "MERGE (d:Domain" in cyphers
    assert "MERGE (doc:Document" in cyphers
    assert "MERGE (c:Chunk" in cyphers
    assert "MERGE (t:Topic" in cyphers
    assert "MERGE (doc)-[:BELONGS_TO]->(d)" in cyphers
    assert "MERGE (c)-[:PART_OF]->(doc)" in cyphers
    assert "MERGE (c)-[:COVERS]->(t)" in cyphers
    assert "MERGE (t)-[:REFINES]->(d)" in cyphers

