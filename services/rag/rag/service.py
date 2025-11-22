from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
from uuid import uuid4

import numpy as np
from sqlalchemy import Select, create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from .chunker import TextChunk, chunk_text
from .config import Settings, get_settings
from .embeddings import EmbeddingBackend, get_backend
from .loader import RawDocument, load_path
from .models import Base, Chunk, Document


@dataclass
class SearchHit:
    document_id: str
    content: str
    score: float
    metadata: dict


class RagService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        embedding_backend: EmbeddingBackend,
        chunk_size: int,
        chunk_overlap: int,
        max_results: int,
    ):
        self._session_factory = session_factory
        self._backend = embedding_backend
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._max_results = max_results

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "RagService":
        settings = settings or get_settings()
        engine = create_engine(settings.database_url, future=True)
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine, future=True)
        backend = get_backend(settings.embedding_backend, settings.embedding_dim)
        return cls(
            session_factory=session_factory,
            embedding_backend=backend,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            max_results=settings.max_search_results,
        )

    def ingest_files(self, paths: Sequence[Path], metadata: dict | None = None) -> list[str]:
        document_ids: list[str] = []
        for path in paths:
            documents = load_path(path)
            for raw in documents:
                doc_id = self._upsert_raw_document(raw, metadata)
                document_ids.append(doc_id)
        return document_ids

    def upsert_inline_documents(self, documents: Sequence[dict]) -> list[str]:
        ids: list[str] = []
        for doc in documents:
            text = doc.get("text", "")
            if not text.strip():
                continue
            metadata = doc.get("metadata", {})
            source_path = doc.get("source_path")
            doc_id = doc.get("document_id") or str(uuid4())
            raw = RawDocument(text=text, metadata={**metadata, "source_path": source_path})
            ids.append(self._upsert_raw_document(raw, extra_metadata={"document_id": doc_id}))
        return ids

    def search(self, query: str, limit: int | None = None) -> list[SearchHit]:
        vector = np.array(self._backend.embed(query), dtype=np.float32)
        max_results = limit or self._max_results
        with self._session_factory() as session:
            rows = session.execute(self._chunk_query()).all()
        hits: list[SearchHit] = []
        for chunk, document in rows:
            embedding = np.array(chunk.embedding, dtype=np.float32)
            score = _cosine_similarity(vector, embedding)
            hits.append(
                SearchHit(
                    document_id=document.id,
                    content=chunk.content,
                    score=float(score),
                    metadata={**document.metadata, **chunk.metadata},
                )
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:max_results]

    def _upsert_raw_document(self, raw: RawDocument, extra_metadata: dict | None = None) -> str:
        metadata = {**raw.metadata}
        metadata.update(extra_metadata or {})
        doc_id = metadata.get("document_id") or str(uuid4())
        chunks = chunk_text(raw.text, chunk_size=self._chunk_size, overlap=self._chunk_overlap)
        chunk_models = self._build_chunks(doc_id, chunks, metadata)
        with self._session_factory() as session:
            document = self._get_or_create_document(session, doc_id, metadata)
            session.execute(delete(Chunk).where(Chunk.document_id == document.id))
            session.add_all(chunk_models)
            session.commit()
        return doc_id

    def _get_or_create_document(self, session: Session, doc_id: str, metadata: dict) -> Document:
        document = session.get(Document, doc_id)
        if document is None:
            document = Document(id=doc_id)
            session.add(document)
        document.metadata = {**(document.metadata or {}), **metadata}
        document.source_path = metadata.get("source_path")
        document.source_type = metadata.get("kind", document.source_type or "inline")
        session.flush()
        return document

    def _build_chunks(self, document_id: str, chunks: Iterable[TextChunk], metadata: dict) -> list[Chunk]:
        models: list[Chunk] = []
        for chunk in chunks:
            embedding = self._backend.embed(chunk.content)
            models.append(
                Chunk(
                    document_id=document_id,
                    position=chunk.index,
                    content=chunk.content,
                    embedding=embedding,
                    metadata={"chunk_index": chunk.index, **metadata},
                )
            )
        return models

    def _chunk_query(self) -> Select[tuple[Chunk, Document]]:
        return select(Chunk, Document).join(Document, Chunk.document_id == Document.id)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
