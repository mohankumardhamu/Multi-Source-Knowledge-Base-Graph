from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from kg_rag_api.agent.agent import Agent
from ..db import session_scope


router = APIRouter(prefix="/v1/agent", tags=["agent"])


def get_db() -> Session:
    with session_scope() as s:
        yield s


class AskRequest(BaseModel):
    query: str
    mode: str = Field(pattern=r"^(qa|tutor|interview)$")
    domain: Optional[str] = None
    topic: Optional[str] = None
    difficulty: str = Field(default="medium", pattern=r"^(easy|medium|hard)$")
    seed: int = 42


@router.post("/ask")
def ask(body: AskRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    agent = Agent(lambda: db)
    if body.mode in ("qa", "tutor"):
        res = agent.answer(body.query, domain=body.domain)
        if "error" in res:
            raise HTTPException(status_code=404, detail=res.get("message", "No answer"))
        if body.mode == "tutor":
            res["plan"] = agent.plan(body.query)
        return res
    elif body.mode == "interview":
        dom = (body.domain or "default").lower()
        return agent.interview(dom, body.topic, body.difficulty, n=5, seed=body.seed)
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")
