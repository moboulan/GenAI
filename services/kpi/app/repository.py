from __future__ import annotations

from datetime import datetime, timedelta, timezone

import statistics

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from .models import Measurement


def _window_filter(stmt: Select, tag: str, start_ts: datetime) -> Select:
    return stmt.where(Measurement.tag == tag).where(Measurement.ts >= start_ts)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def aggregate_window(
    session: Session,
    tag: str,
    window_minutes: int,
    reference_ts: datetime | None = None,
):
    if reference_ts is None:
        reference_ts = datetime.now(timezone.utc)
    start_ts = reference_ts - timedelta(minutes=window_minutes)

    agg_stmt = select(
        func.avg(Measurement.value).label("avg"),
        func.min(Measurement.value).label("min"),
        func.max(Measurement.value).label("max"),
        func.count(Measurement.value).label("count"),
    )
    agg_stmt = _window_filter(agg_stmt, tag, start_ts)
    row = session.execute(agg_stmt).one()

    latest_stmt = (
        select(Measurement.value, Measurement.ts)
        .order_by(Measurement.ts.desc())
        .limit(1)
    )
    latest_stmt = _window_filter(latest_stmt, tag, start_ts)
    latest = session.execute(latest_stmt).first()

    earliest_stmt = (
        select(Measurement.value, Measurement.ts)
        .order_by(Measurement.ts.asc())
        .limit(1)
    )
    earliest_stmt = _window_filter(earliest_stmt, tag, start_ts)
    earliest = session.execute(earliest_stmt).first()

    values_stmt = select(Measurement.value)
    values_stmt = _window_filter(values_stmt, tag, start_ts)
    values = [row.value for row in session.execute(values_stmt)]
    stddev = statistics.stdev(values) if len(values) >= 2 else None

    return {
        "tag": tag,
        "window_minutes": window_minutes,
        "start_ts": start_ts,
        "end_ts": reference_ts,
        "avg": row.avg,
        "minimum": row.min,
        "maximum": row.max,
        "stddev": stddev,
        "latest_value": latest.value if latest else None,
        "latest_ts": _ensure_utc(latest.ts if latest else None),
        "earliest_value": earliest.value if earliest else None,
        "earliest_ts": _ensure_utc(earliest.ts if earliest else None),
        "total_points": int(row.count or 0),
    }
