from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from .config import get_settings
from .schemas import DocumentBatch, SearchRequest, SearchResponse, UpsertResponse
from .service import RagService

app = FastAPI(title="RAG Service")


@lru_cache(maxsize=1)
def get_service() -> RagService:
    return RagService.from_settings()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upsert", response_model=UpsertResponse)
def upsert_documents(payload: DocumentBatch, service: RagService = Depends(get_service)) -> UpsertResponse:
    if not payload.documents:
        raise HTTPException(status_code=400, detail="No documents provided")
    ids = service.upsert_inline_documents([doc.model_dump() for doc in payload.documents])
    return UpsertResponse(document_ids=ids)


@app.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, service: RagService = Depends(get_service)) -> SearchResponse:
    results = service.search(payload.query, limit=payload.limit)
    payload_hits = [
        {
            "chunk_id": hit.chunk_id,
            "document_id": hit.document_id,
            "text": hit.text,
            "score": hit.score,
            "metadata": hit.metadata,
        }
        for hit in results
    ]
    return SearchResponse.from_hits(payload_hits)
