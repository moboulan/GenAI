from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

from orchestrator.agent import AgentOrchestrator
from orchestrator.api import app, get_agent
from orchestrator.clients import KpiClient, MockableLLM, RagClient, RagHit
from orchestrator.config import Settings
from orchestrator.rules import RulesEngine


class DummyRag(RagClient):
    def __init__(self, hits):
        super().__init__(base_url="http://test", timeout=1)
        self._hits = hits

    async def search(self, query: str, limit: int | None = None):
        return self._hits


class DummyKpi(KpiClient):
    def __init__(self, payload):
        super().__init__(base_url="http://test", timeout=1)
        self._payload = payload

    async def fetch_formula(self, name: str, window: int = 30):
        payload = dict(self._payload)
        payload.setdefault("name", name)
        return payload


@contextmanager
def override_agent(agent: AgentOrchestrator):
    app.dependency_overrides[get_agent] = lambda: agent
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_agent, None)


def test_chat_endpoint_returns_sources():
    hits = [
        RagHit(
            chunk_id="c1",
            document_id="doc1",
            text="Procédure en cas de baisse",
            score=0.8,
            metadata={"title": "Procédure"},
        )
    ]
    settings = Settings()
    rules_path = Path(__file__).resolve().parents[1] / "rules" / "guardrails.yml"
    agent = AgentOrchestrator(
        settings=settings,
        rag=DummyRag(hits),
        kpi=DummyKpi({"value": 92, "unit": "%"}),
        llm=MockableLLM(),
        rules=RulesEngine(path=rules_path),
    )

    with override_agent(agent):
        client = TestClient(app)
        payload = {"message": "rendement"}
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] in {"kpi", "mixed"}
        assert data["sources"]


def test_chat_rejects_short_message():
    client = TestClient(app)
    response = client.post("/chat", json={"message": "hi"})
    assert response.status_code == 422
```