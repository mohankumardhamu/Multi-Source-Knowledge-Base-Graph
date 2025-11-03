from __future__ import annotations

from fastapi.testclient import TestClient

from kg_rag_api.main import app


def test_generate_questions_deterministic(monkeypatch):
    # Mock retriever
    from kg_rag_common import retriever

    hits = [
        {
            "id": "p1",
            "score": 0.9,
            "payload": {
                "doc_id": "d1",
                "chunk_id": "c1",
                "page_from": 1,
                "page_to": 1,
                "content": "This discusses HTTP servers and async handling."
            },
        },
        {
            "id": "p2",
            "score": 0.8,
            "payload": {
                "doc_id": "d2",
                "chunk_id": "c2",
                "page_from": 2,
                "page_to": 3,
                "content": "def solve(): pass\n# example"
            },
        },
    ]

    monkeypatch.setattr(retriever, "vector_search", lambda q, d, top_k=10, filters=None: hits)

    # Mock graph driver writes (no-ops)
    from kg_rag_common import graph as graph_util

    class FakeTx:
        def run(self, *args, **kwargs):
            class R:
                def consume(self):
                    return None
            return R()

    class FakeSession:
        def execute_write(self, fn):
            fn(FakeTx())

        def close(self):
            pass

    class FakeDriver:
        def session(self):
            return FakeSession()

    monkeypatch.setattr(graph_util, "get_driver", lambda: FakeDriver())

    client = TestClient(app)
    body = {"domain": "python", "difficulty": "medium", "n": 3, "seed": 123}
    r1 = client.post("/v1/generate/questions", json=body)
    assert r1.status_code == 200
    out1 = r1.json()
    r2 = client.post("/v1/generate/questions", json=body)
    assert r2.status_code == 200
    out2 = r2.json()
    # Deterministic across calls with same seed
    assert out1 == out2
    # Contains required fields
    q = out1[0]
    assert set(q.keys()) == {"id", "type", "prompt", "options", "answer", "explanation", "rubric", "provenance"}

