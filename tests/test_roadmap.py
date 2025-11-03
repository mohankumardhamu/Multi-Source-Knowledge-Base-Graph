from __future__ import annotations

from fastapi.testclient import TestClient

from kg_rag_api.main import app


def test_generate_and_get_roadmap(monkeypatch):
    from kg_rag_common import graph as graph_util

    topics = [
        {"name": "intro to algorithms"},
        {"name": "data structures"},
        {"name": "advanced algorithms"},
        {"name": "networking basics"},
    ]

    created_nodes = {}
    created_edges = set()

    class FakeResult:
        def __init__(self, rows, keys):
            self._rows = rows
            self._keys = keys

        def __iter__(self):
            for r in self._rows:
                yield r

        def keys(self):
            return self._keys

        def single(self):
            return self._rows[0] if self._rows else None

    class FakeTx:
        def run(self, cypher, **params):
            c = " ".join(cypher.split())
            if "MERGE (r:RoadmapNode" in c:
                created_nodes[params["id"]] = {
                    "id": params["id"],
                    "domain": params["domain"],
                    "topic": params["topic"],
                    "label": params["label"],
                    "week": params["week"],
                    "hours": params["hours"],
                    "level": params["level"],
                }
            if "MERGE (a)-[:REQUIRES]->(b)" in c:
                created_edges.add((params["src"], params["dst"]))
            class R:
                def consume(self):
                    return None
            return R()

    class FakeSession:
        def execute_write(self, fn):
            fn(FakeTx())

        def run(self, cypher, **params):
            c = " ".join(cypher.split())
            if c.startswith("MATCH (t:Topic"):
                # return topic names
                return ({"name": t["name"]} for t in topics)
            if c.startswith("MATCH (r:RoadmapNode {domain:") and "RETURN r.id" in c:
                rows = [
                    {"id": n["id"], "label": n["label"], "topic": n["topic"], "week": n["week"], "hours": n["hours"], "level": n["level"]}
                    for n in created_nodes.values()
                ]
                return rows
            if c.startswith("MATCH (a:RoadmapNode {domain:") and ":REQUIRES" in c:
                rows = [{"src": s, "dst": t} for (s, t) in created_edges]
                return rows
            return []

        def close(self):
            pass

    class FakeDriver:
        def session(self):
            return FakeSession()

    monkeypatch.setattr(graph_util, "get_driver", lambda: FakeDriver())

    client = TestClient(app)

    # Generate
    req = {"domain": "python", "horizon_weeks": 4, "hours_per_week": 6}
    r = client.post("/v1/generate/roadmap", json=req)
    assert r.status_code == 200
    data = r.json()
    assert data["nodes"]
    assert data["edges"]

    # Get
    g = client.get("/v1/roadmaps/python")
    assert g.status_code == 200
    out = g.json()
    assert out["nodes"]
    assert out["edges"]

