from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List

from .schema import Tag


@dataclass
class Observation:
    tag: Tag
    value: float
    timestamp: datetime

    def as_dict(self) -> Dict[str, str | float]:
        return {
            "tag": self.tag.name,
            "topic": self.tag.topic,
            "unit": self.tag.unit,
            "value": round(self.value, 4),
            "ts": self.timestamp.isoformat(),
        }


class SimSignalGenerator:
    """Generates synthetic values for a list of tags."""

    def __init__(self, tags: Iterable[Tag], seed: int | None = None) -> None:
        self.tags: List[Tag] = list(tags)
        self.random = random.Random(seed)

    def _next_value(self, tag: Tag) -> float:
        drift = self.random.uniform(-tag.noise, tag.noise)
        candidate = tag.baseline + drift
        return tag.clamp(candidate)

    def next_batch(self) -> List[Observation]:
        ts = datetime.now(timezone.utc)
        return [Observation(tag=t, value=self._next_value(t), timestamp=ts) for t in self.tags]

    def stream(self, interval: float = 1.0):
        while True:
            yield self.next_batch()
            if interval > 0:
                time.sleep(interval)
