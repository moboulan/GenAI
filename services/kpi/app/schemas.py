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


class FormulaMetadata(BaseModel):
    name: str
    label: str
    unit: str
    description: str
    default_window_minutes: int = Field(..., gt=0)
    required_tags: list[str]


class FormulaComputation(BaseModel):
    name: str
    label: str
    unit: str
    description: str
    expression: str
    window_minutes: int = Field(..., gt=0)
    value: float
    inputs: dict[str, KpiResponse]
