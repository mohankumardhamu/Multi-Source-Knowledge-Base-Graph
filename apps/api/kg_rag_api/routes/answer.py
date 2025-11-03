from __future__ import annotations

import statistics
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from kg_rag_common.classify import detect_language
from kg_rag_common.retriever import vector_search
from kg_rag_common.reranker import CosineReranker
from kg_rag_common import graph as graph_util


router = APIRouter(prefix="/v1", tags=["answer"])

_LAT_SAMPLES: List[float] = []
_MAX_SAMPLES = 200


class AnswerRequest(BaseModel):
    query: str
    domain: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=50)


class Citation(BaseModel):
    doc_id: str
    page_from: Optional[int] = None
    page_to: Optional[int] = None
    heading_path: Optional[List[str]] = None


class AnswerResponse(BaseModel):
    answer: str
    citations: List[Citation]
    metrics: Dict[str, float]


def _classify_domain_from_query(q: str) -> str:
    lang = (detect_language(q) or "default").lower()
    return lang


def _neighbors_from_graph(domain: str, chunk_ids: List[str]) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    """Return (topic->definition, topic->prereqs)."""
    driver = graph_util.get_driver()
    topics: Set[str] = set()
    prereqs: Dict[str, List[str]] = {}
    definitions: Dict[str, str] = {}
    with graph_util.session_ctx(driver) as session:
        # topics covered by chunks
        res = session.run(
            """
            UNWIND $ids AS cid
            MATCH (c:Chunk {id: cid})-[:COVERS]->(t:Topic)-[:REFINES]->(d:Domain {name: $domain})
            RETURN DISTINCT t.name AS topic
            """,
            ids=chunk_ids,
            domain=domain,
        )
        for r in res:
            topics.add(r["topic"])

        # prerequisites via roadmap nodes
        res2 = session.run(
            """
            UNWIND $topics AS tname
            MATCH (r:RoadmapNode {domain: $domain, topic: tname})-[:REQUIRES]->(p:RoadmapNode {domain: $domain})
            RETURN tname AS topic, collect(DISTINCT p.topic) AS prereqs
            """,
            topics=list(topics),
            domain=domain,
        )
        for r in res2:
            prereqs[r["topic"]] = list(r["prereqs"] or [])

        # definitions from Concept nodes if present
        res3 = session.run(
            """
            UNWIND $all AS tname
            OPTIONAL MATCH (c:Concept {name: tname})
            RETURN tname AS topic, c.definition AS def
            """,
            all=list(topics | set(v for vs in prereqs.values() for v in vs)),
        )
        for r in res3:
            if r["def"]:
                definitions[r["topic"]] = r["def"]

    # synthesize missing definitions
    for t in list(topics) + [p for vs in prereqs.values() for p in vs]:
        if t not in definitions:
            definitions[t] = f"{t.title()} is a key concept in {domain}."
    return definitions, prereqs


def _compose_answer(query: str, hits: List[Dict[str, Any]], defs: Dict[str, str], prereqs: Dict[str, List[str]]) -> Tuple[str, List[Citation]]:
    lines: List[str] = []
    lines.append(f"Answer to: {query}\n")
    used: int = 0
    citations: List[Citation] = []
    for h in hits[:3]:
        p = h.get("payload", {})
        snippet = (p.get("content") or "").strip()
        if snippet:
            snippet = snippet.split("\n")[0]
        lines.append(f"- {snippet}")
        citations.append(
            Citation(
                doc_id=str(p.get("doc_id")),
                page_from=p.get("page_from"),
                page_to=p.get("page_to"),
                heading_path=p.get("heading_path") or [],
            )
        )
        used += 1
    # next topics
    next_topics: List[str] = []
    for vs in prereqs.values():
        next_topics.extend(vs)
    next_topics = sorted(set(next_topics))[:5]
    if next_topics:
        lines.append("\nNext topics to study:")
        for t in next_topics:
            lines.append(f"- {t}: {defs.get(t, '')}")
    return "\n".join(lines).strip(), citations


@router.post("/answer", response_model=AnswerResponse)
def answer(body: AnswerRequest):
    t0 = time.perf_counter()
    domain = (body.domain or _classify_domain_from_query(body.query)).lower()
    hits = vector_search(body.query, domain, top_k=body.top_k)
    rer = CosineReranker()
    hits = rer.rerank(body.query, hits)
    chunk_ids = [h.get("payload", {}).get("chunk_id") for h in hits if h.get("payload", {}).get("chunk_id")]
    defs, prereqs = _neighbors_from_graph(domain, chunk_ids)
    text, citations = _compose_answer(body.query, hits, defs, prereqs)
    t1 = time.perf_counter()

    # latency metrics
    dur_ms = (t1 - t0) * 1000.0
    _LAT_SAMPLES.append(dur_ms)
    if len(_LAT_SAMPLES) > _MAX_SAMPLES:
        del _LAT_SAMPLES[: len(_LAT_SAMPLES) - _MAX_SAMPLES]
    samples = sorted(_LAT_SAMPLES)
    def pct(p: float) -> float:
        if not samples:
            return 0.0
        k = max(0, min(len(samples) - 1, int(round(p * (len(samples) - 1)))))
        return samples[k]

    metrics = {"p50_ms": pct(0.50), "p95_ms": pct(0.95)}
    return AnswerResponse(answer=text, citations=citations, metrics=metrics)

