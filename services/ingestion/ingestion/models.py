from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass
class Measurement:
    tag: str
    topic: str
    unit: str
    value: float
    timestamp: datetime

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "Measurement":
        return cls(
            tag=payload["tag"],
            topic=payload["topic"],
            unit=payload["unit"],
            value=float(payload["value"]),
            timestamp=parse_timestamp(payload["ts"]),
        )
