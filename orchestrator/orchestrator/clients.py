from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class RagHit:
    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: dict[str, Any]


class RagClient:
    def __init__(self, base_url: str, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def search(self, query: str, limit: int | None = None) -> list[RagHit]:
        payload: dict[str, Any] = {"query": query}
        if limit is not None:
            payload["limit"] = limit
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            response = await client.post("/search", json=payload)
            response.raise_for_status()
        data = response.json().get("hits", [])
        return [RagHit(**hit) for hit in data]


class KpiClient:
    def __init__(self, base_url: str, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def fetch_formula(self, name: str, window: int = 30) -> dict[str, Any]:
        params = {"window": window}
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            response = await client.get(f"/kpi/formulas/{name}", params=params)
            response.raise_for_status()
        return response.json()

    async def fetch_trend(self, tag: str, window: int = 30) -> dict[str, Any]:
        params = {"tag": tag, "window": window}
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            response = await client.get("/kpi/trend", params=params)
            response.raise_for_status()
        return response.json()


class MockableLLM:
    def summarize(self, *, question: str, kpi: dict | None, hits: list[RagHit]) -> str:
        parts: list[str] = []
        if kpi:
            value = kpi.get("value")
            unit = kpi.get("unit", "")
            parts.append(f"KPI {kpi.get('name', 'inconnu')}: {value} {unit}".strip())
        if hits:
            snippet_lines = [f"[{hit.document_id}] {hit.text}" for hit in hits[:2]]
            parts.append("Documents: " + " | ".join(snippet_lines))
        if not parts:
            parts.append("Aucune donnée exploitable, veuillez préciser la question.")
        return "\n".join(parts)
