from __future__ import annotations

from typing import Iterable, Sequence

from sqlalchemy import Column, MetaData, String, Table, create_engine
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.engine import Engine
from sqlalchemy.sql import insert

from .models import Measurement

METADATA = MetaData()

MEASUREMENTS = Table(
    "measurements",
    METADATA,
    Column("ts", TIMESTAMP(timezone=True), nullable=False, primary_key=True),
    Column("tag", String, nullable=False, primary_key=True),
    Column("topic", String, nullable=False),
    Column("unit", String, nullable=False),
    Column("value", DOUBLE_PRECISION, nullable=False),
)


class TimescaleWriter:
    """Simple writer that persists measurements using SQLAlchemy."""

    def __init__(self, engine: Engine | str):
        self.engine = create_engine(engine) if isinstance(engine, str) else engine
        METADATA.create_all(self.engine)

    def write(self, measurements: Sequence[Measurement]) -> None:
        if not measurements:
            return
        rows = [
            {
                "ts": m.timestamp,
                "tag": m.tag,
                "topic": m.topic,
                "unit": m.unit,
                "value": m.value,
            }
            for m in measurements
        ]
        stmt = insert(MEASUREMENTS).values(rows)
        with self.engine.begin() as conn:
            conn.execute(stmt)


def decode_batch(payloads: Iterable[dict]) -> list[Measurement]:
    return [Measurement.from_payload(item) for item in payloads]
