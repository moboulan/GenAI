from __future__ import annotations

from datetime import datetime
from typing import Literal

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
    earliest_value: float | None = None
    earliest_ts: datetime | None = None
    stddev: float | None = None
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


class TrendResponse(BaseModel):
    tag: str
    window_minutes: int = Field(..., gt=0)
    start_ts: datetime
    end_ts: datetime
    earliest_value: float
    earliest_ts: datetime
    latest_value: float
    latest_ts: datetime
    delta: float
    slope_per_min: float
    percent_change: float | None
    direction: Literal["up", "down", "flat"]


class AnomalyResponse(BaseModel):
    tag: str
    window_minutes: int = Field(..., gt=0)
    start_ts: datetime
    end_ts: datetime
    latest_value: float
    latest_ts: datetime | None
    avg: float
    stddev: float
    z_score: float
    threshold: float
    is_anomaly: bool
    total_points: int = Field(..., ge=0)
