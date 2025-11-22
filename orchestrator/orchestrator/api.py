from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI

from .agent import AgentOrchestrator
from .clients import KpiClient, MockableLLM, RagClient
from .config import Settings, get_settings
from .rules import RulesEngine
from .schemas import ChatRequest, ChatResponse

app = FastAPI(title="TSP Orchestrator")


@lru_cache(maxsize=1)
def get_agent(settings: Settings | None = None) -> AgentOrchestrator:
    settings = settings or get_settings()
    rag = RagClient(base_url=settings.rag_base_url, timeout=settings.request_timeout)
    kpi = KpiClient(base_url=settings.kpi_base_url, timeout=settings.request_timeout)
    llm = MockableLLM()
    rules = RulesEngine()
    return AgentOrchestrator(settings=settings, rag=rag, kpi=kpi, llm=llm, rules=rules)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, agent: AgentOrchestrator = Depends(get_agent)) -> ChatResponse:
    return await agent.handle(payload)
