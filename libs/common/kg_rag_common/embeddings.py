from __future__ import annotations

import hashlib
import os
import random
from abc import ABC, abstractmethod
from typing import Iterable, List


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:  # vector size
        raise NotImplementedError

    @abstractmethod
    def embed_texts(self, texts: Iterable[str]) -> List[list[float]]:
        raise NotImplementedError


class LocalFakeProvider(EmbeddingProvider):
    """Deterministic local provider for testing/dev.

    Generates vectors based on a hash of the input text for stability.
    """

    def __init__(self, dim: int = 384):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: Iterable[str]) -> List[list[float]]:
        vecs: List[list[float]] = []
        for t in texts:
            h = hashlib.sha256((t or "").encode("utf-8")).digest()
            rnd = random.Random(h)
            vecs.append([rnd.random() for _ in range(self._dim)])
        return vecs


_REGISTRY: dict[str, EmbeddingProvider] = {
    "local-fake": LocalFakeProvider(),
}


def get_provider(name: str | None = None) -> EmbeddingProvider:
    key = name or os.getenv("KG_EMBED_PROVIDER", "local-fake")
    prov = _REGISTRY.get(key)
    if prov is None:
        # placeholder for real providers: raise with clear message
        raise KeyError(f"Unknown embedding provider: {key}")
    return prov

