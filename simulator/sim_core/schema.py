from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import yaml


@dataclass(frozen=True)
class Tag:
    name: str
    topic: str
    unit: str
    min: float
    max: float
    baseline: float
    noise: float

    def clamp(self, value: float) -> float:
        """Clamp value between configured min/max."""
        return max(self.min, min(self.max, value))


def load_tags(path: str | Path) -> List[Tag]:
    """Load tag definitions from a YAML file."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    tag_items: Iterable[dict] = data.get("tags", [])
    return [Tag(**item) for item in tag_items]
