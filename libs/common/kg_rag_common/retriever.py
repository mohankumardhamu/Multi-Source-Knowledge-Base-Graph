from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from libs.common.kg_rag_common.embeddings import get_provider
from libs.common.kg_rag_common.qdrant_util import get_client, ensure_collection


def _to_condition(key: str, value: Any):
    # Scalars -> MatchValue
    if isinstance(value, (str, int, float, bool)):
        return qm.FieldCondition(key=key, match=qm.MatchValue(value=value))
    # List/Tuple -> MatchAny
    if isinstance(value, (list, tuple)):
        return qm.FieldCondition(key=key, match=qm.MatchAny(any=list(value)))
    # Dict operators: {in: [...]} or range {gte, lte, gt, lt}
    if isinstance(value, dict):
        if not value:
            return None
        if "in" in value or "$in" in value:
            vals = value.get("in") or value.get("$in") or []
            return qm.FieldCondition(key=key, match=qm.MatchAny(any=list(vals)))
        rng_keys = {"gte", "lte", "gt", "lt"} & set(value.keys())
        if rng_keys:
            rng = qm.Range(**{k: value[k] for k in rng_keys})
            return qm.FieldCondition(key=key, range=rng)
    return None


def _build_filter(filters: Optional[Dict[str, Any]]) -> Optional[qm.Filter]:
    if not filters:
        return None
    must: List[qm.Condition] = []
    for k, v in filters.items():
        cond = _to_condition(k, v)
        if cond is not None:
            must.append(cond)
    return qm.Filter(must=must) if must else None


def vector_search(
    query: str,
    domain: str,
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    provider = get_provider()
    vec = provider.embed_texts([query])[0]
    client: QdrantClient = get_client()
    collection = f"vectors_{(domain or 'default').lower()}"
    ensure_collection(client, collection, provider.dimension)

    res = client.search(
        collection_name=collection,
        query_vector=vec,
        limit=top_k,
        with_payload=True,
        query_filter=_build_filter(filters),
    )
    hits: List[Dict[str, Any]] = []
    for r in res:
        hits.append({
            "id": r.id,
            "score": float(r.score),
            "payload": dict(r.payload or {}),
        })
    return hits


def rerank_stub(query: str, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Placeholder: return as-is (already by vector score)
    return hits
