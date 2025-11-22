from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from .models import Measurement


def _window_filter(stmt: Select, tag: str, start_ts: datetime) -> Select:
    return stmt.where(Measurement.tag == tag).where(Measurement.ts >= start_ts)


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

    def _ensure_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    return {
        "tag": tag,
        "window_minutes": window_minutes,
        "start_ts": start_ts,
        "end_ts": reference_ts,
        "avg": row.avg,
        "minimum": row.min,
        "maximum": row.max,
        "latest_value": latest.value if latest else None,
        "latest_ts": _ensure_utc(latest.ts if latest else None),
        "total_points": int(row.count or 0),
    }
