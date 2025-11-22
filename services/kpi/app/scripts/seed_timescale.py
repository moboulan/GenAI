from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Measurement

TAG_CONFIG = {
    "reactor_temperature": {"topic": "process/reactor/temperature", "unit": "C", "baseline": 85.0, "drift": 0.05, "noise": 1.2},
    "acid_flow": {"topic": "process/acid/flow", "unit": "t_h", "baseline": 62.0, "drift": 0.02, "noise": 0.8},
    "p2o5_concentration": {"topic": "lab/p2o5", "unit": "pct", "baseline": 45.0, "drift": 0.01, "noise": 0.3},
    "free_acidity": {"topic": "lab/free_acidity", "unit": "pct", "baseline": 1.4, "drift": -0.005, "noise": 0.05},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed TimescaleDB with synthetic KPI measurements")
    parser.add_argument("--dsn", default="postgresql+psycopg://tsp:tsp_pass@localhost:5432/tsp", help="SQLAlchemy DSN for TimescaleDB")
    parser.add_argument("--hours", type=int, default=6, help="Number of hours of history to generate")
    parser.add_argument("--interval-minutes", type=int, default=5, help="Sampling interval in minutes")
    parser.add_argument("--truncate", action="store_true", help="Truncate measurements table before seeding")
    parser.add_argument("--seed", type=int, default=1234, help="Random seed for reproducibility")
    return parser.parse_args()


def generate_rows(end_ts: datetime, hours: int, interval_minutes: int):
    total_points = int((hours * 60) / interval_minutes)
    for idx in range(total_points):
        ts = end_ts - timedelta(minutes=idx * interval_minutes)
        for tag, cfg in TAG_CONFIG.items():
            drift = cfg["drift"] * idx
            jitter = random.uniform(-cfg["noise"], cfg["noise"])
            yield Measurement(
                ts=ts,
                tag=tag,
                topic=cfg["topic"],
                unit=cfg["unit"],
                value=cfg["baseline"] + drift + jitter,
            )


def main():
    args = parse_args()
    random.seed(args.seed)
    engine = create_engine(args.dsn, future=True)
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    rows = list(generate_rows(now, args.hours, args.interval_minutes))

    with Session(engine) as session:
        if args.truncate:
            session.execute(delete(Measurement))
        session.add_all(rows)
        session.commit()
    print(f"Seeded {len(rows)} rows into measurements table")


if __name__ == "__main__":
    main()
