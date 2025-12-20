from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from libs.common.kg_rag_common.models import Document, IngestionStatus
from libs.common.kg_rag_common import graph as graph_util
from libs.common.kg_rag_common.settings import get_settings
from apps.workers.kg_rag_workers.worker import make_celery  # type: ignore
from ..db import session_scope


router = APIRouter(tags=["ui"])


def get_db() -> Session:
    with session_scope() as s:
        yield s


def _layout(title: str, body: str) -> HTMLResponse:
    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8'/>
      <meta name='viewport' content='width=device-width, initial-scale=1'>
      <title>{title}</title>
      <script src="https://unpkg.com/htmx.org@1.9.12"></script>
      <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50 text-gray-900">
      <nav class="bg-white shadow mb-6">
        <div class="max-w-5xl mx-auto px-4 py-3 flex gap-4">
          <a href="/admin" class="text-blue-600">Admin</a>
          <a href="/explore/graph" class="text-blue-600">Explore Graph</a>
          <a href="/learn/roadmap?domain=python" class="text-blue-600">Learn Roadmap</a>
        </div>
      </nav>
      <main class="max-w-5xl mx-auto px-4">{body}</main>
    </body>
    </html>
    """
    return HTMLResponse(html)


@router.get("/admin", response_class=HTMLResponse)
def admin_page(db: Session = Depends(get_db)):
    docs: List[Document] = db.query(Document).order_by(Document.created_at.desc()).all()
    status_map = {
        s.document_id: s for s in db.query(IngestionStatus).all()
    }
    rows = []
    for d in docs:
        st = status_map.get(d.id)
        s_val = st.status if st else d.status
        rows.append(f"""
          <tr id="doc-{d.id}" class="border-b">
            <td class="p-2 text-xs">{d.id}</td>
            <td class="p-2">{d.title}</td>
            <td class="p-2">{d.domain or ''}</td>
            <td class="p-2">{s_val}</td>
            <td class="p-2 text-xs">{d.created_at}</td>
            <td class="p-2">
              <button class="px-3 py-1 bg-blue-600 text-white rounded"
                hx-post="/admin/ingest/{d.id}/rerun" hx-target="#doc-{d.id}" hx-swap="outerHTML">Re-run</button>
            </td>
          </tr>
        """)
    table = f"""
      <h1 class="text-2xl font-semibold mb-4">Ingestion Jobs</h1>
      <table class="w-full bg-white shadow rounded">
        <thead class="bg-gray-100">
          <tr>
            <th class="p-2 text-left">ID</th>
            <th class="p-2 text-left">Title</th>
            <th class="p-2 text-left">Domain</th>
            <th class="p-2 text-left">Status</th>
            <th class="p-2 text-left">Created</th>
            <th class="p-2 text-left">Actions</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows) if rows else '<tr><td class="p-4" colspan="6">No documents.</td></tr>'}
        </tbody>
      </table>
    """
    return _layout("Admin", table)


@router.post("/admin/ingest/{doc_id}/rerun", response_class=HTMLResponse)
def rerun_ingest(doc_id: str, db: Session = Depends(get_db)):
    d = db.get(Document, doc_id)
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    celery = make_celery()
    celery.send_task("ingest.process", args=[str(d.id)])
    # Return updated row snippet
    return HTMLResponse(f"""
      <tr id="doc-{d.id}" class="border-b bg-yellow-50">
        <td class="p-2 text-xs">{d.id}</td>
        <td class="p-2">{d.title}</td>
        <td class="p-2">{d.domain or ''}</td>
        <td class="p-2">queued</td>
        <td class="p-2 text-xs">{d.created_at}</td>
        <td class="p-2">
          <button class="px-3 py-1 bg-blue-600 text-white rounded"
            hx-post="/admin/ingest/{d.id}/rerun" hx-target="#doc-{d.id}" hx-swap="outerHTML">Re-run</button>
        </td>
      </tr>
    """)


@router.get("/explore/graph", response_class=HTMLResponse)
def explore_graph_page():
    canned = [
        ("Topics per Domain", "MATCH (t:Topic)-[:REFINES]->(d:Domain) RETURN t.name, d.name LIMIT 50"),
        ("Chunk->Topic edges", "MATCH (c:Chunk)-[:COVERS]->(t:Topic) RETURN c.id, t.name LIMIT 50"),
    ]
    opts = "".join([f"<option value=\"{q}\">{label}</option>" for (label, q) in canned])
    body = f"""
      <h1 class=\"text-2xl font-semibold mb-4\">Explore Graph</h1>
      <div class=\"bg-white p-4 rounded shadow\">
        <label class=\"block mb-2\">Canned query</label>
        <select id=\"cypher\" class=\"border p-2 w-full mb-3\" onchange=\"document.getElementById('cypherText').value=this.value\">{opts}</select>
        <textarea id=\"cypherText\" class=\"border p-2 w-full h-24\">MATCH (t:Topic)-[:REFINES]->(d:Domain) RETURN t.name, d.name LIMIT 50</textarea>
        <button class=\"mt-3 px-3 py-1 bg-blue-600 text-white rounded\" hx-post=\"/v1/search/graph\" hx-target=\"#result\" hx-vals=\"js:{{cypher: document.getElementById('cypherText').value}}\">Run</button>
        <pre id=\"result\" class=\"mt-4 text-xs overflow-auto\"></pre>
      </div>
    """
    return _layout("Explore Graph", body)


@router.get("/learn/roadmap", response_class=HTMLResponse)
def learn_roadmap_page(domain: Optional[str] = None):
    if not domain:
        domain = "python"
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
        items = [
            {
                "id": r["id"],
                "label": r["label"],
                "topic": r["topic"],
                "week": int(r["week"]),
                "hours": int(r["hours"]),
            }
            for r in res_nodes
        ]
    # group by week
    weeks: dict[int, list[dict]] = {}
    for it in items:
        weeks.setdefault(it["week"], []).append(it)
    parts = [f"<h1 class='text-2xl font-semibold mb-4'>Roadmap: {domain.title()}</h1>"]
    for w in sorted(weeks.keys()):
        parts.append(f"<h2 class='text-xl mt-4 mb-2'>Week {w}</h2>")
        parts.append("<ul class='list-disc ml-6'>")
        for it in weeks[w]:
            parts.append(f"<li>{it['label']} <span class='text-gray-500 text-sm'>({it['hours']}h)</span></li>")
        parts.append("</ul>")
    if not parts:
        parts.append("<p>No roadmap yet. Generate one from /v1/generate/roadmap.</p>")
    return _layout("Learn Roadmap", "".join(parts))
