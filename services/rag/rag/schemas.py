from __future__ import annotations

from typing import List, Sequence

from pydantic import BaseModel, Field


class DocumentPayload(BaseModel):
    text: str = Field(..., min_length=1)
    metadata: dict[str, str] | None = None


class DocumentBatch(BaseModel):
    documents: List[DocumentPayload]


class UpsertResponse(BaseModel):
    document_ids: List[str]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int | None = Field(default=None, gt=0)


class SearchHit(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    hits: List[SearchHit]

    @classmethod
    def from_hits(cls, hits: Sequence[dict]) -> "SearchResponse":
        return cls(hits=[SearchHit(**hit) for hit in hits])
