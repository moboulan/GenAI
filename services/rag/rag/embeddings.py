from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import Iterable

import numpy as np

try:  # Optional heavy dependency
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    SentenceTransformer = None


class EmbeddingBackend(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class HashedEmbeddingBackend(EmbeddingBackend):
    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = []
        idx = 0
        while len(values) < self.dim:
            byte = digest[idx % len(digest)]
            values.append((byte / 255.0) - 0.5)
            idx += 1
        array = np.array(values, dtype=np.float32)
        array = array / (np.linalg.norm(array) + 1e-9)
        return array.tolist()


class SentenceTransformerBackend(EmbeddingBackend):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers is not installed")
        self._model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        vector = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()


def get_backend(backend_name: str, dim: int) -> EmbeddingBackend:
    name = backend_name.lower()
    if name in {"auto", "hashed"}:
        if name == "auto" and SentenceTransformer is not None:
            return SentenceTransformerBackend()
        return HashedEmbeddingBackend(dim=dim)
    if name == "sentence-transformer" or name.startswith("st:"):
        model = backend_name.split(":", maxsplit=1)[-1] if ":" in backend_name else "all-MiniLM-L6-v2"
        return SentenceTransformerBackend(model_name=model)
    raise ValueError(f"Unknown embedding backend: {backend_name}")
