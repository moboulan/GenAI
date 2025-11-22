from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class IntentPrediction:
    label: str
    confidence: float
    kpi_name: str | None = None


KPI_KEYWORDS = {
    "rendement": "rendement",
    "taux": "rendement",
    "acide": "acidite_libre",
    "humidite": "humidite",
}
DOCUMENT_KEYWORDS = {"procedure", "logigramme", "instruction", "comment"}


def normalize(text: str) -> str:
    return text.lower().strip()


def classify_intent(message: str) -> IntentPrediction:
    text = normalize(message)
    for key, kpi_name in KPI_KEYWORDS.items():
        if key in text:
            return IntentPrediction(label="kpi", confidence=0.72, kpi_name=kpi_name)
    if any(keyword in text for keyword in DOCUMENT_KEYWORDS):
        return IntentPrediction(label="documents", confidence=0.63)
    return IntentPrediction(label="mixed", confidence=0.5)


def extract_keywords(message: str, dictionary: dict[str, str]) -> list[str]:
    text = normalize(message)
    return [value for key, value in dictionary.items() if key in text]
