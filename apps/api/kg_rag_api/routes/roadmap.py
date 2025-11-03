from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from kg_rag_common import graph as graph_util


router = APIRouter(prefix="/v1", tags=["roadmap"])


class RoadmapRequest(BaseModel):
    domain: str
    horizon_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=60)


class RoadmapNodeOut(BaseModel):
    id: str
    label: str
    topic: str
    week: int
    hours: int
    level: int


class RoadmapEdgeOut(BaseModel):
    source: str
    target: str  # edge: source requires target (source -> target)


class RoadmapResponse(BaseModel):
    nodes: List[RoadmapNodeOut]
    edges: List[RoadmapEdgeOut]


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "topic"


def _fetch_topics(domain: str) -> List[str]:
    driver = graph_util.get_driver()
    with graph_util.session_ctx(driver) as session:
        res = session.run(
            """
            MATCH (t:Topic)-[:REFINES]->(d:Domain {name: $domain})
            RETURN t.name AS name
            """,
            domain=domain,
        )
        return [r["name"] for r in res]


ALIASES: Dict[str, List[str]] = {
    "algorithms": ["algo", "algorithm"],
    "data structures": ["ds", "structure"],
    "networking": ["network", "http", "tcp", "udp"],
    "databases": ["db", "database", "sql"],
    "concurrency": ["parallel", "async", "threads", "locking"],
}


def _is_prereq(a: str, b: str) -> bool:
    la = a.lower()
    lb = b.lower()
    if la == lb:
        return False
    # intro/basic/fundamentals precede others that contain the term
    if ("intro" in la or "basic" in la or "fundament" in la) and any(x in lb for x in la.split()):
        return True
    # containment heuristic
    if la in lb and len(la) >= 4:
        return True
    # alias mapping
    for canon, aliases in ALIASES.items():
        if la in [canon] + aliases:
            if canon in lb or any(al in lb for al in aliases):
                return True
    return False


def _build_dag(topics: List[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
    # edges: (src -> dst) meaning src requires dst? we build requires edges later; here we use prereq -> topic
    edges: List[Tuple[str, str]] = []
    for a in topics:
        for b in topics:
            if _is_prereq(a, b):
                edges.append((a, b))

    # ensure acyclicity: greedily drop edges that cause cycles using DFS
    adj: Dict[str, List[str]] = {t: [] for t in topics}
    def creates_cycle(u: str, v: str) -> bool:
        # check if path exists v -> u
        stack = [v]
        seen = set()
        while stack:
            x = stack.pop()
            if x == u:
                return True
            if x in seen:
                continue
            seen.add(x)
            stack.extend(adj.get(x, []))
        return False

    for u, v in edges:
        if not creates_cycle(u, v):
            adj[u].append(v)

    # If no edges, create linear order fallback
    if all(not vs for vs in adj.values()):
        ordered = sorted(topics)
        for i in range(len(ordered) - 1):
            adj[ordered[i]].append(ordered[i + 1])

    # topological order via Kahn
    indeg: Dict[str, int] = {t: 0 for t in topics}
    for u, vs in adj.items():
        for v in vs:
            indeg[v] += 1
    queue: List[str] = [t for t, d in indeg.items() if d == 0]
    order: List[str] = []
    while queue:
        node = sorted(queue).pop(0)  # deterministic
        queue.remove(node)
        order.append(node)
        for v in adj.get(node, []):
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    # recover remaining nodes (cycles) if any
    for t in topics:
        if t not in order:
            order.append(t)

    final_edges: List[Tuple[str, str]] = []
    for u, vs in adj.items():
        for v in vs:
            final_edges.append((u, v))
    return order, final_edges


def _estimate_hours(topic: str) -> int:
    base = 3
    t = topic.lower()
    if "advanced" in t:
        base += 3
    if "intro" in t or "basic" in t:
        base -= 1
    base += min(3, max(0, len(t.split()) - 2))
    return max(2, min(10, base))


def _schedule(order: List[str], edges: List[Tuple[str, str]], horizon_weeks: int, hpw: int) -> Tuple[List[RoadmapNodeOut], List[RoadmapEdgeOut]]:
    # map topic to week by filling capacity
    week = 1
    used = 0
    nodes: List[RoadmapNodeOut] = []
    id_map: Dict[str, str] = {}
    for topic in order:
        hours = _estimate_hours(topic)
        if used + hours > hpw and week < horizon_weeks:
            week += 1
            used = 0
        used += hours
        rid = f"{_slug(topic)}-{week}"
        id_map[topic] = rid
        nodes.append(RoadmapNodeOut(id=rid, label=topic.title(), topic=topic, week=week, hours=hours, level=week))

    edge_out: List[RoadmapEdgeOut] = []
    for u, v in edges:
        # requires edge from v (dependent) to u (prereq)
        if u in id_map and v in id_map:
            edge_out.append(RoadmapEdgeOut(source=id_map[v], target=id_map[u]))
    return nodes, edge_out


def _persist(domain: str, nodes: List[RoadmapNodeOut], edges: List[RoadmapEdgeOut]):
    driver = graph_util.get_driver()
    with graph_util.session_ctx(driver) as session:
        def write_tx(tx):
            for n in nodes:
                tx.run(
                    """
                    MERGE (r:RoadmapNode {id: $id})
                    SET r.domain = $domain,
                        r.topic = $topic,
                        r.label = $label,
                        r.week = $week,
                        r.hours = $hours,
                        r.level = $level
                    """,
                    id=n.id,
                    domain=domain,
                    topic=n.topic,
                    label=n.label,
                    week=n.week,
                    hours=n.hours,
                    level=n.level,
                )
            for e in edges:
                tx.run(
                    """
                    MATCH (a:RoadmapNode {id: $src}), (b:RoadmapNode {id: $dst})
                    MERGE (a)-[:REQUIRES]->(b)
                    """,
                    src=e.source,
                    dst=e.target,
                )
        graph_util.execute_write(session, write_tx)


@router.post("/generate/roadmap", response_model=RoadmapResponse)
def generate_roadmap(body: RoadmapRequest):
    topics = _fetch_topics(body.domain)
    if not topics:
        raise HTTPException(status_code=404, detail="No topics found for domain")
    order, edges = _build_dag(topics)
    nodes, edge_out = _schedule(order, edges, body.horizon_weeks, body.hours_per_week)
    _persist(body.domain, nodes, edge_out)
    return RoadmapResponse(nodes=nodes, edges=edge_out)


@router.get("/roadmaps/{domain}", response_model=RoadmapResponse)
def get_roadmap(domain: str):
    driver = graph_util.get_driver()
    with graph_util.session_ctx(driver) as session:
        res_nodes = session.run(
            """
            MATCH (r:RoadmapNode {domain: $domain})
            RETURN r.id AS id, r.label AS label, r.topic AS topic, r.week AS week, r.hours AS hours, r.level AS level
            ORDER BY r.week, r.label
            """,
            domain=domain,
        )
        nodes = [RoadmapNodeOut(id=r["id"], label=r["label"], topic=r["topic"], week=int(r["week"]), hours=int(r["hours"]), level=int(r["level"])) for r in res_nodes]
        res_edges = session.run(
            """
            MATCH (a:RoadmapNode {domain: $domain})-[:REQUIRES]->(b:RoadmapNode {domain: $domain})
            RETURN a.id AS src, b.id AS dst
            """,
            domain=domain,
        )
        edges = [RoadmapEdgeOut(source=r["src"], target=r["dst"]) for r in res_edges]
    return RoadmapResponse(nodes=nodes, edges=edges)

