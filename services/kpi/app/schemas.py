from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class KpiResponse(BaseModel):
    tag: str
    window_minutes: int = Field(..., gt=0)
    start_ts: datetime
    end_ts: datetime
    avg: float | None
    minimum: float | None
    maximum: float | None
    latest_value: float | None
    latest_ts: datetime | None
    total_points: int
