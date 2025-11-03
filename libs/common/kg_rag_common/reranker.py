from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Reranker(ABC):
    @abstractmethod
    def rerank(self, query: str, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raise NotImplementedError


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _bow(text: str) -> Dict[str, float]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    weights: Dict[str, float] = {}
    for t in tokens:
        weights[t] = weights.get(t, 0.0) + 1.0
    # l2 normalize
    norm = math.sqrt(sum(v * v for v in weights.values())) or 1.0
    for k in list(weights.keys()):
        weights[k] /= norm
    return weights


def _cos(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    return sum(val * b.get(key, 0.0) for key, val in a.items())


class CosineReranker(Reranker):
    def rerank(self, query: str, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        qv = _bow(query)
        scored: List[tuple[float, Dict[str, Any]]] = []
        for h in hits:
            payload = h.get("payload", {})
            content = payload.get("content") or payload.get("text") or ""
            cv = _bow(content)
            s = 0.75 * _cos(qv, cv) + 0.25 * float(h.get("score") or 0.0)
            scored.append((s, h))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [h for _, h in scored]

