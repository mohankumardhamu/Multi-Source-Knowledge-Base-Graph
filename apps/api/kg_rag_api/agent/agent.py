from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import random

from sqlalchemy.orm import Session

from libs.common.kg_rag_common.classify import detect_language
from libs.common.kg_rag_common.retriever import vector_search
from libs.common.kg_rag_common.reranker import CosineReranker
from libs.common.kg_rag_common import graph as graph_util
from libs.common.kg_rag_common.models import Chunk


class Agent:
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._reranker = CosineReranker()

    # Tools
    def vector_search(self, query: str, domain: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None):
        return vector_search(query, domain, top_k=top_k, filters=filters)

    def run_cypher(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        driver = graph_util.get_driver()
        with graph_util.session_ctx(driver) as session:
            result = session.run(cypher, **(params or {}))
            records = list(result)
            keys = list(result.keys())
            return [{k: r.get(k) for k in keys} for r in records]

    def fetch_chunk_text(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        session: Session = self._session_factory()
        try:
            row = session.get(Chunk, chunk_id)
            if not row:
                return None
            return {
                "id": str(row.id),
                "document_id": str(row.document_id),
                "content": row.content,
                "page_from": row.page_from,
                "page_to": row.page_to,
                "heading_path": (row.heading_path or {}).get("path", []) if isinstance(row.heading_path, dict) else [],
            }
        finally:
            session.close()

    def plan(self, query: str) -> List[str]:
        return [
            "Clarify the goal and constraints",
            "Retrieve relevant chunks",
            "Synthesize an answer from citations",
            "Suggest next topics to study",
        ]

    def _neighbors_from_graph(self, domain: str, chunk_ids: List[str]) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
        driver = graph_util.get_driver()
        topics: set[str] = set()
        prereqs: Dict[str, List[str]] = {}
        defs: Dict[str, str] = {}
        with graph_util.session_ctx(driver) as session:
            res = session.run(
                """
                UNWIND $ids AS cid
                MATCH (c:Chunk {id: cid})-[:COVERS]->(t:Topic)-[:REFINES]->(d:Domain {name: $domain})
                RETURN DISTINCT t.name AS topic
                """,
                ids=chunk_ids,
                domain=domain,
            )
            topics.update([r["topic"] for r in res])
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
                    defs[r["topic"]] = r["def"]
        for t in list(topics) + [p for vs in prereqs.values() for p in vs]:
            if t not in defs:
                defs[t] = f"{t.title()} is a key concept in {domain}."
        return defs, prereqs

    def answer(self, query: str, domain: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        dom = (domain or (detect_language(query) or "default")).lower()
        hits = self.vector_search(query, dom, top_k=top_k)
        hits = self._reranker.rerank(query, hits)
        if not hits:
            return {"error": "no_results", "message": "No relevant content found."}
        top = hits[0]
        # fail-closed if low confidence and no content
        if float(top.get("score") or 0.0) < 0.05 and not (top.get("payload", {}).get("content")):
            return {"error": "low_confidence", "message": "Unable to answer confidently."}
        chunk_ids = [h.get("payload", {}).get("chunk_id") for h in hits if h.get("payload", {}).get("chunk_id")]
        defs, prereqs = self._neighbors_from_graph(dom, chunk_ids)
        bullets: List[str] = []
        citations: List[Dict[str, Any]] = []
        for h in hits[:3]:
            p = h.get("payload", {})
            txt = (p.get("content") or "").split("\n")[0]
            if txt:
                bullets.append(f"- {txt}")
            citations.append({
                "doc_id": p.get("doc_id"),
                "page_from": p.get("page_from"),
                "page_to": p.get("page_to"),
                "heading_path": p.get("heading_path") or [],
            })
        next_topics = sorted({x for vs in prereqs.values() for x in vs})[:5]
        if next_topics:
            bullets.append("Next topics to study:")
            for t in next_topics:
                bullets.append(f"- {t}: {defs.get(t, '')}")
        return {"answer": "\n".join(bullets).strip(), "citations": citations, "domain": dom}

    # mode: interview
    def interview(self, domain: str, topic: Optional[str], difficulty: str, n: int = 5, seed: int = 42) -> Dict[str, Any]:
        driver = graph_util.get_driver()
        with graph_util.session_ctx(driver) as session:
            if topic:
                res = session.run(
                    """
                    MATCH (q:Question {difficulty: $difficulty})-[:BELONGS_TO]->(d:Domain {name: $domain})
                    OPTIONAL MATCH (q)-[:ASSESS]->(t:Topic {name: $topic})
                    RETURN q.id AS id, q.type AS type, q.prompt AS prompt, q.options AS options, q.answer AS answer, q.rubric AS rubric
                    """,
                    domain=domain, topic=topic, difficulty=difficulty,
                )
            else:
                res = session.run(
                    """
                    MATCH (q:Question {difficulty: $difficulty})-[:BELONGS_TO]->(d:Domain {name: $domain})
                    RETURN q.id AS id, q.type AS type, q.prompt AS prompt, q.options AS options, q.answer AS answer, q.rubric AS rubric
                    """,
                    domain=domain, difficulty=difficulty,
                )
            rows = list(res)
            rnd = random.Random(seed)
            rnd.shuffle(rows)
            sel = rows[:n]
            items: List[Dict[str, Any]] = []
            for r in sel:
                items.append({
                    "id": r["id"],
                    "type": r["type"],
                    "prompt": r["prompt"],
                    "options": r.get("options"),
                    "answer": r.get("answer"),
                    "rubric": r.get("rubric"),
                    "grade": None,
                })
            return {"questions": items}

