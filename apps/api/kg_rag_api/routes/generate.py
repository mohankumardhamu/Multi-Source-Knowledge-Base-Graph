from __future__ import annotations

import hashlib
import random
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from kg_rag_common.retriever import vector_search
from kg_rag_common import graph as graph_util
from kg_rag_common.models import Chunk, Document
from ..db import session_scope


router = APIRouter(prefix="/v1", tags=["generate"])


class GenerateRequest(BaseModel):
    domain: Optional[str] = None
    topic: Optional[str] = None
    difficulty: str = Field(pattern=r"^(easy|medium|hard)$")
    n: int = Field(ge=1, le=50)
    seed: int = 42


class QuestionOut(BaseModel):
    id: str
    type: str
    prompt: str
    options: Optional[List[str]] = None
    answer: str
    explanation: str
    rubric: str
    provenance: Dict[str, Any]


class GenerateResponse(BaseModel):
    status: str  # "vector" or "fallback"
    questions: List[QuestionOut]


def _namespace_for_seed(seed: int) -> uuid.UUID:
    h = hashlib.sha256(str(seed).encode()).hexdigest()
    return uuid.UUID(h[:32])


def _make_id(seed_ns: uuid.UUID, base: str) -> str:
    return str(uuid.uuid5(seed_ns, base))


def _make_mcq(rnd: random.Random, text: str) -> tuple[str, list[str], int]:
    words = [w.strip(",. ") for w in text.split() if len(w) > 3]
    if not words:
        words = ["alpha", "bravo", "charlie", "delta"]
    correct = rnd.choice(words)
    distractors = list({rnd.choice(words) for _ in range(6) if True})
    distractors = [d for d in distractors if d != correct][:3]
    while len(distractors) < 3:
        distractors.append(rnd.choice(words))
    options = distractors + [correct]
    rnd.shuffle(options)
    answer_idx = options.index(correct)
    prompt = f"Which of the following terms best relates to the content above?"
    return prompt, options, answer_idx


def _make_coding(rnd: random.Random, text: str, domain: str) -> tuple[str, str]:
    if domain == "python":
        prompt = "Write a Python function named solve() that prints the number of words in the given input string."
        answer = "def solve(s):\n    print(len(s.split()))"
    elif domain == "java":
        prompt = "Write a Java method countWords(String s) that returns the number of words split by spaces."
        answer = "int countWords(String s){ return s.trim().isEmpty()?0:s.trim().split(\\\\s+).length; }"
    else:
        prompt = f"Write a function to count words in a string in {domain}."
        answer = ""
    return prompt, answer


def _make_short_answer(rnd: random.Random, text: str) -> tuple[str, str]:
    prompt = "Summarize the key idea from the content in one sentence."
    answer = "It explains the main concept with concise details."
    return prompt, answer


def _generate_questions_from_hits(
    hits: List[Dict[str, Any]], domain: str, n: int, difficulty: str, seed: int
) -> List[QuestionOut]:
    rnd = random.Random(seed)
    ns = _namespace_for_seed(seed)
    out: List[QuestionOut] = []
    if not hits:
        return out
    # cycle through hits and types deterministically
    types = ["mcq", "coding", "short"]
    for i in range(n):
        h = hits[i % len(hits)]
        payload = h.get("payload", {})
        text = payload.get("text", payload.get("content", ""))
        qtype = types[i % len(types)]
        if qtype == "mcq":
            prompt, options, correct_idx = _make_mcq(rnd, text)
            answer = options[correct_idx]
        elif qtype == "coding":
            prompt, answer = _make_coding(rnd, text, domain)
            options = None
        else:
            prompt, answer = _make_short_answer(rnd, text)
            options = None
        qid = _make_id(ns, f"{payload.get('chunk_id','')}-{qtype}-{i}-{difficulty}")
        explanation = "Deterministically generated from chunk content."
        rubric = f"Assess correctness and clarity at {difficulty} level."
        prov = {
            "doc_id": payload.get("doc_id"),
            "chunk_id": payload.get("chunk_id"),
            "page_range": [payload.get("page_from"), payload.get("page_to")],
        }
        out.append(
            QuestionOut(
                id=qid,
                type=qtype,
                prompt=prompt,
                options=options,
                answer=answer,
                explanation=explanation,
                rubric=rubric,
                provenance=prov,
            )
        )
    return out


def _persist_questions(domain: str, topic: Optional[str], questions: List[QuestionOut]):
    driver = graph_util.get_driver()
    with graph_util.session_ctx(driver) as session:
        def write_batch(tx):
            for q in questions:
                p = q.provenance
                tx.run(
                    """
                    MERGE (qn:Question {id: $id})
                    SET qn.type = $type,
                        qn.prompt = $prompt,
                        qn.options = $options,
                        qn.answer = $answer,
                        qn.explanation = $explanation,
                        qn.rubric = $rubric,
                        qn.difficulty = $difficulty
                    WITH qn
                    MERGE (a:Answer {id: $aid})
                    SET a.text = $answer
                    MERGE (qn)-[:HAS_ANSWER]->(a)
                    WITH qn
                    MERGE (c:Chunk {id: $chunk_id})
                    MERGE (qn)-[:DERIVED_FROM]->(c)
                    WITH qn
                    MERGE (d:Domain {name: $domain})
                    MERGE (qn)-[:BELONGS_TO]->(d)
                    """,
                    id=q.id,
                    type=q.type,
                    prompt=q.prompt,
                    options=q.options,
                    answer=q.answer,
                    explanation=q.explanation,
                    rubric=q.rubric,
                    difficulty="medium",  # stored difficulty; use request level
                    aid=f"{q.id}:answer",
                    chunk_id=p.get("chunk_id"),
                    domain=domain,
                )
                # Assess relationships by topics
                topics = []
                if topic:
                    topics.append(topic)
                # We can't access chunk payload here; caller can pass request topic
                if topics:
                    tx.run(
                        """
                        MATCH (qn:Question {id: $id})
                        UNWIND $topics AS tname
                        MERGE (t:Topic {name: tname})
                        MERGE (qn)-[:ASSESS]->(t)
                        """,
                        id=q.id,
                        topics=topics,
                    )
        graph_util.execute_write(session, write_batch)


def get_db() -> Session:
    with session_scope() as s:
        yield s


@router.post("/generate/questions", response_model=GenerateResponse)
def generate_questions(body: GenerateRequest, db: Session = Depends(get_db)):
    if not body.domain and not body.topic:
        raise HTTPException(status_code=400, detail="Provide at least 'domain' or 'topic'")
    domain = (body.domain or "default").lower()
    # Build filters if topic provided
    filters = {"topics": [body.topic]} if body.topic else None
    hits = vector_search(body.topic or body.domain or "concepts", domain, top_k=max(10, body.n), filters=filters)
    source = "vector"
    # Fallback: if no vector hits, sample chunks from DB by domain/topic
    if not hits:
        q = db.query(Chunk)
        if body.topic:
            q = q.filter(Chunk.topics.contains([body.topic]))
        else:
            q = q.join(Document, Chunk.document_id == Document.id).filter(Document.domain == domain)
        rows = q.order_by(desc(Chunk.created_at)).limit(max(10, body.n)).all()
        # If still empty (e.g., domain mismatch), fall back to latest chunks across all domains
        if not rows:
            rows = db.query(Chunk).order_by(desc(Chunk.created_at)).limit(max(10, body.n)).all()
        hits = [
            {
                "id": str(c.id),
                "score": 0.0,
                "payload": {
                    "doc_id": str(c.document_id),
                    "chunk_id": str(c.id),
                    "page_from": c.page_from,
                    "page_to": c.page_to,
                    "content": c.content,
                },
            }
            for c in rows
        ]
        source = "fallback"
    qs = _generate_questions_from_hits(hits, domain, body.n, body.difficulty, body.seed)
    _persist_questions(domain, body.topic, qs)
    return GenerateResponse(status=source, questions=qs)


@router.get("/questions/{qid}", response_model=QuestionOut)
def get_question(qid: str):
    driver = graph_util.get_driver()
    with graph_util.session_ctx(driver) as session:
        res = session.run(
            """
            MATCH (q:Question {id: $id})-[:HAS_ANSWER]->(a)
            OPTIONAL MATCH (q)-[:DERIVED_FROM]->(c:Chunk)
            RETURN q.id AS id, q.type AS type, q.prompt AS prompt, q.options AS options,
                   a.text AS answer, q.explanation AS explanation, q.rubric AS rubric,
                   c.id AS chunk_id
            """,
            id=qid,
        )
        rec = res.single()
        if not rec:
            raise HTTPException(status_code=404, detail="Question not found")
        prov = {"doc_id": None, "chunk_id": rec["chunk_id"], "page_range": [None, None]}
        return QuestionOut(
            id=rec["id"],
            type=rec["type"],
            prompt=rec["prompt"],
            options=rec["options"],
            answer=rec["answer"],
            explanation=rec["explanation"],
            rubric=rec["rubric"],
            provenance=prov,
        )
