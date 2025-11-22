from __future__ import annotations

from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from rag.api import app, get_service
from rag.service import SearchHit


class DummyService:
    def __init__(self) -> None:
        self.inline_ids: list[str] = ["doc-123"]
        self.search_result: list[SearchHit] = []
        self.upsert_calls: list[list[dict]] = []
        self.search_calls: list[tuple[str, int | None]] = []

    def upsert_inline_documents(self, documents: list[dict]) -> list[str]:
        self.upsert_calls.append(documents)
        return self.inline_ids

    def search(self, query: str, limit: int | None = None):
        self.search_calls.append((query, limit))
        return self.search_result


@contextmanager
def override_service(service: DummyService):
    app.dependency_overrides[get_service] = lambda: service
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_service, None)


@pytest.fixture
def client():
    service = DummyService()
    with override_service(service):
        with TestClient(app) as http_client:
            yield http_client, service


def test_health_endpoint(client):
    http, _ = client
    response = http.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upsert_requires_documents(client):
    http, _ = client
    response = http.post("/upsert", json={"documents": []})
    assert response.status_code == 400
    assert response.json()["detail"] == "No documents provided"


def test_upsert_returns_service_ids(client):
    http, service = client
    service.inline_ids = ["doc-a", "doc-b"]
    payload = {"documents": [{"text": "hello", "metadata": {"a": "b"}}]}
    response = http.post("/upsert", json=payload)
    assert response.status_code == 200
    assert response.json() == {"document_ids": ["doc-a", "doc-b"]}
    assert service.upsert_calls and service.upsert_calls[0][0]["text"] == "hello"


def test_search_returns_hits(client):
    http, service = client
    service.search_result = [
        SearchHit(
            chunk_id="chunk-1",
            document_id="doc-1",
            text="snippet",
            score=0.42,
            metadata={"origin": "unit"},
        )
    ]
    response = http.post("/search", json={"query": "test"})
    assert response.status_code == 200
    assert response.json()["hits"] == [
        {
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "text": "snippet",
            "score": 0.42,
            "metadata": {"origin": "unit"},
        }
    ]
    assert service.search_calls == [("test", None)]
