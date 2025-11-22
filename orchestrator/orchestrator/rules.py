from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml

from .clients import RagHit


class RulesEngine:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(__file__).resolve().parent.parent / "rules" / "guardrails.yml"
        self._config = self._load()

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        return yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}

    def build_recommendations(self, hits: Iterable[RagHit]) -> list[dict[str, str]]:
        template = self._config.get("recommendation_template", {})
        recs: list[dict[str, str]] = []
        for hit in hits:
            recs.append(
                {
                    "action": hit.metadata.get("action", hit.text[:80]),
                    "impact": template.get("impact", ""),
                    "risks": template.get("risks", ""),
                    "prerequisites": template.get("prerequisites", ""),
                }
            )
        return recs[:3]

    def evaluate_safety(self, kpi_payload: dict | None) -> list[str]:
        notices: list[str] = []
        if not kpi_payload:
            return notices
        value = kpi_payload.get("value")
        name = kpi_payload.get("name")
        safety_config = self._config.get("safety_notices", [])
        for rule in safety_config:
            condition = rule.get("condition", "")
            if _matches(condition, value, name):
                notices.append(rule.get("message", ""))
        return notices


def _matches(condition: str, value: float | None, name: str | None) -> bool:
    if value is None or name is None:
        return False
    if "rendement" in condition.lower() and name != "rendement":
        return False
    if "<" in condition:
        threshold = float(condition.split("<")[-1].strip())
        return value < threshold
    if ">" in condition:
        threshold = float(condition.split(">")[-1].strip())
        return value > threshold
    return False
