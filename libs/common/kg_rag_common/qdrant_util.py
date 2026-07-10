from __future__ import annotations

from typing import Any, Iterable, List, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from libs.common.kg_rag_common.settings import get_settings


def get_client() -> QdrantClient:
    s = get_settings()
    return QdrantClient(url=s.qdrant_url, prefer_grpc=False, timeout=30.0)


def ensure_collection(client: QdrantClient, name: str, vector_size: int) -> None:
    collections = client.get_collections().collections
    if any(c.name == name for c in collections):
        return
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def upsert_vectors(
    client: QdrantClient,
    collection: str,
    points: Iterable[Tuple[str, list[float], dict[str, Any]]],
) -> None:
    qpoints: List[PointStruct] = []
    for pid, vec, payload in points:
        qpoints.append(PointStruct(id=pid, vector=vec, payload=payload))
    if qpoints:
        client.upsert(collection_name=collection, points=qpoints)


def count_vectors_for_doc(client: QdrantClient, collection: str, doc_id: str) -> int:
    try:
        result = client.count(
            collection_name=collection,
            count_filter=Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]),
            exact=True,
        )
        return int(result.count)
    except Exception:
        return 0
