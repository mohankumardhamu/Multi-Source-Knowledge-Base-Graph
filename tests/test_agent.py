from __future__ import annotations

from fastapi.testclient import TestClient

from kg_rag_api.main import app


def test_agent_qa_routes_and_tools(monkeypatch):
    # Mock vector search to return hits with content
    from kg_rag_common import retriever
    hits = [
        {"id": "p1", "score": 0.2, "payload": {"doc_id": "d1", "chunk_id": "c1", "page_from": 1, "page_to": 1, "heading_path": ["H"], "content": "Example content about HTTP and servers."}},
        {"id": "p2", "score": 0.1, "payload": {"doc_id": "d2", "chunk_id": "c2", "page_from": 2, "page_to": 3, "heading_path": ["H2"], "content": "Concurrency using threads."}},
    ]
    monkeypatch.setattr(retriever, "vector_search", lambda q, d, top_k=5, filters=None: hits)

    # Mock graph neighbors
    from kg_rag_common import graph as graph_util

    class FakeSession:
        def run(self, cypher, **params):
            c = " ".join(cypher.split()).upper()
            if "RETURN DISTINCT T.NAME" in c:
                return [{"topic": "networking"}]
            if "RETURN TNAME AS TOPIC, COLLECT(DISTINCT P.TOPIC) AS PREREQS" in c:
                return [{"topic": "networking", "prereqs": ["http"]}]
            if "RETURN TNAME AS TOPIC, C.DEFINITION AS DEF" in c:
                return [{"topic": "http", "def": "HTTP is a protocol."}]
            return []

        def close(self):
            pass

    class FakeDriver:
        def session(self):
            return FakeSession()

    monkeypatch.setattr(graph_util, "get_driver", lambda: FakeDriver())

    client = TestClient(app)
    res = client.post("/v1/agent/ask", json={"query": "How do HTTP servers work?", "mode": "qa", "domain": "python"})
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data and "citations" in data
    assert any("Next topics" in line for line in data["answer"].split("\n"))


def test_agent_interview_selects_questions(monkeypatch):
    from kg_rag_common import graph as graph_util
    # create fake questions
    rows = [
        {"id": f"q{i}", "type": "mcq", "prompt": f"P{i}", "options": ["a","b"], "answer": "a", "rubric": "correct==a"}
        for i in range(10)
    ]

    class FakeSession:
        def run(self, cypher, **params):
            return rows

        def close(self):
            pass

    class FakeDriver:
        def session(self):
            return FakeSession()

    monkeypatch.setattr(graph_util, "get_driver", lambda: FakeDriver())

    client = TestClient(app)
    res = client.post("/v1/agent/ask", json={"query": "net", "mode": "interview", "domain": "python", "difficulty": "easy"})
    assert res.status_code == 200
    data = res.json()
    assert "questions" in data and len(data["questions"]) == 5

