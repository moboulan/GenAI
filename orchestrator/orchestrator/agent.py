from __future__ import annotations

from dataclasses import dataclass

from .clients import KpiClient, MockableLLM, RagClient
from .config import Settings
from .intent import IntentPrediction, classify_intent
from .rules import RulesEngine
from .schemas import ChatRequest, ChatResponse, RecommendationBlock, SourcePayload


def _build_sources(hits):
    return [
        SourcePayload(
            type="document",
            title=hit.metadata.get("title", hit.document_id),
            excerpt=hit.text,
            metadata={"document_id": hit.document_id, **hit.metadata},
        )
        for hit in hits
    ]


def _wrap_recommendations(engine: RulesEngine, hits):
    recs = engine.build_recommendations(hits)
    return [RecommendationBlock(**rec) for rec in recs]


@dataclass
class AgentOrchestrator:
    settings: Settings
    rag: RagClient
    kpi: KpiClient
    llm: MockableLLM
    rules: RulesEngine

    async def handle(self, request: ChatRequest) -> ChatResponse:
        prediction = classify_intent(request.message)
        limit = request.max_sources or self.settings.max_rag_hits
        rag_hits = []
        kpi_payload = None

        if prediction.label in {"documents", "mixed"}:
            rag_hits = await self.rag.search(request.message, limit=limit)
        if prediction.label in {"kpi", "mixed"} and prediction.kpi_name:
            kpi_payload = await self.kpi.fetch_formula(prediction.kpi_name)
            kpi_payload["name"] = prediction.kpi_name

        answer = self.llm.summarize(question=request.message, kpi=kpi_payload, hits=rag_hits)
        sources = _build_sources(rag_hits)
        recommendations = _wrap_recommendations(self.rules, rag_hits or [])
        notices = self.rules.evaluate_safety(kpi_payload)
        if notices:
            answer += "\n" + "\n".join(f"⚠️ {notice}" for notice in notices)

        return ChatResponse(
            intent=prediction.label,
            confidence=prediction.confidence,
            answer=answer,
            sources=sources,
            recommendations=recommendations,
        )
