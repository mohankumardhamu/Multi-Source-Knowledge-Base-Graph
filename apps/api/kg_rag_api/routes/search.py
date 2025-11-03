from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import boto3
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from redis import Redis

from kg_rag_common.retriever import vector_search, rerank_stub
from kg_rag_common.settings import get_settings
from kg_rag_common import graph as graph_util
from kg_rag_common.models import Document
from sqlalchemy.orm import Session

from ..db import session_scope


router = APIRouter(prefix="/v1/search", tags=["search"])


def _redis() -> Redis:
    s = get_settings()
    return Redis.from_url(str(s.redis_dsn))


def _rate_limit(key_prefix: str, request: Request, limit: int = 30, window_sec: int = 60):
    r = _redis()
    ip = request.client.host if request.client else "unknown"
    key = f"rl:{key_prefix}:{ip}"
    pipe = r.pipeline()
    pipe.incr(key, 1)
    pipe.expire(key, window_sec, nx=True)
    count, _ = pipe.execute()
    if int(count) > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


def _s3_client():
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint_url,
        aws_access_key_id=s.s3_access_key,
        aws_secret_access_key=s.s3_secret_key,
    )


def _signed_url(bucket: str, key: str, expires: int = 3600) -> str:
    s3 = _s3_client()
    return s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
    )


def get_db() -> Session:
    with session_scope() as s:
        yield s


class VectorSearchRequest(BaseModel):
    query: str
    domain: str
    top_k: int = Field(default=10, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = None


class VectorSearchHit(BaseModel):
    score: float
    payload: Dict[str, Any]
    preview_url: str


class VectorSearchResponse(BaseModel):
    hits: List[VectorSearchHit]


@router.post("/vector", response_model=VectorSearchResponse)
def vector_endpoint(req: Request, body: VectorSearchRequest, db: Session = Depends(get_db)):
    _rate_limit("vector", req)

    hits = vector_search(body.query, body.domain, body.top_k, body.filters)
    hits = rerank_stub(body.query, hits)

    # gather document info for signing URLs
    doc_map: Dict[str, Document] = {}
    for h in hits:
        doc_id = h["payload"].get("doc_id")
        if doc_id and doc_id not in doc_map:
            d = db.get(Document, doc_id)
            if d:
                doc_map[doc_id] = d

    out: List[VectorSearchHit] = []
    for h in hits:
        p = h["payload"]
        doc_id = p.get("doc_id")
        d = doc_map.get(doc_id)
        if d:
            url = _signed_url(d.s3_bucket, d.s3_key)
        else:
            url = ""
        out.append(VectorSearchHit(score=h["score"], payload=p, preview_url=url))
    return VectorSearchResponse(hits=out)


class GraphSearchRequest(BaseModel):
    cypher: str
    params: Optional[Dict[str, Any]] = None


class GraphSearchResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]


def _is_readonly_cypher(cypher: str) -> bool:
    c = (cypher or "").strip().upper()
    forbidden = ["CREATE ", "MERGE ", "DELETE ", "SET ", "REMOVE ", "LOAD ", "CALL ", "DROP "]
    if any(f in c for f in forbidden):
        return False
    # basic requirement: starts with MATCH/RETURN/WITH
    return c.startswith("MATCH") or c.startswith("RETURN") or c.startswith("WITH")


@router.post("/graph", response_model=GraphSearchResponse)
def graph_endpoint(req: Request, body: GraphSearchRequest):
    _rate_limit("graph", req)
    if not _is_readonly_cypher(body.cypher):
        raise HTTPException(status_code=400, detail="Cypher must be read-only")

    driver = graph_util.get_driver()
    with graph_util.session_ctx(driver) as session:
        result = session.run(body.cypher, **(body.params or {}))
        records = list(result)
        columns = list(result.keys())
        rows: List[List[Any]] = []
        for r in records:
            rows.append([r.get(k) for k in columns])
    return GraphSearchResponse(columns=columns, rows=rows)

