from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from redis import Redis

from kg_rag_common.settings import get_settings
from kg_rag_common.qdrant_util import get_client as get_qdrant_client
from kg_rag_common import graph as graph_util
from kg_rag_common.models import Document
from ..db import session_scope, engine as sa_engine


router = APIRouter(prefix="/v1/admin", tags=["admin-api"])


def get_db() -> Session:
    with session_scope() as s:
        yield s


def _redis() -> Redis:
    s = get_settings()
    return Redis.from_url(str(s.redis_dsn))


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Documents list
    docs = [
        {
            "id": str(d.id),
            "title": d.title,
            "domain": d.domain,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in db.query(Document).order_by(Document.created_at.desc()).all()
    ]

    # Qdrant collections and total points
    qdrant = {"collections": [], "total_points": 0}
    try:
        qclient = get_qdrant_client()
        collections = qclient.get_collections().collections
        for c in collections:
            name = c.name
            try:
                info = qclient.get_collection(name)
                # newer clients use points_count
                count = getattr(info, "points_count", None)
                if count is None:
                    # fallback
                    count = getattr(info.status, "points_count", 0) if hasattr(info, "status") else 0
            except Exception:
                count = 0
            qdrant["collections"].append({"name": name, "count": int(count or 0)})
            qdrant["total_points"] += int(count or 0)
    except Exception as e:
        qdrant = {"error": str(e)}

    # Neo4j counts
    try:
        driver = graph_util.get_driver()
        with graph_util.session_ctx(driver) as gsession:
            nodes_count = gsession.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            rels_count = gsession.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        neo4j = {"nodes": int(nodes_count or 0), "relationships": int(rels_count or 0)}
    except Exception as e:
        neo4j = {"error": str(e)}

    # Redis keys
    r = _redis()
    redis_info = {"keys": int(r.dbsize())}

    # Postgres table row counts (public schema)
    tables: List[Dict[str, Any]] = []
    with sa_engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            )
        )
        table_names = [row[0] for row in result]
        total_rows = 0
        for tname in table_names:
            try:
                cnt = conn.execute(text(f'SELECT COUNT(1) FROM "{tname}"')).scalar() or 0
            except Exception:
                cnt = 0
            tables.append({"table": tname, "rows": int(cnt)})
            total_rows += int(cnt)
    postgres = {"tables": tables, "total_rows": total_rows}

    return {
        "documents": docs,
        "qdrant": qdrant,
        "neo4j": neo4j,
        "redis": redis_info,
        "postgres": postgres,
    }
