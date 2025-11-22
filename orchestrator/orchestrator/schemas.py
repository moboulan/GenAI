from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=3)
    session_id: Optional[str] = None
    max_sources: Optional[int] = Field(default=None, gt=0)


class SourcePayload(BaseModel):
    type: str
    title: str
    excerpt: str
    metadata: dict


class RecommendationBlock(BaseModel):
    action: str
    impact: str
    risks: str
    prerequisites: str


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    answer: str
    sources: List[SourcePayload]
    recommendations: List[RecommendationBlock]