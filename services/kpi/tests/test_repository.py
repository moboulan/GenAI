from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Measurement
from app.repository import aggregate_window


def setup_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)


def seed_data(session: Session, base_ts: datetime):
    rows = [
        Measurement(
            ts=base_ts - timedelta(minutes=10),
            tag="reactor_temperature",
            topic="process/reactor/temperature",
            unit="C",
            value=80.0,
        ),
        Measurement(
            ts=base_ts - timedelta(minutes=5),
            tag="reactor_temperature",
            topic="process/reactor/temperature",
            unit="C",
            value=90.0,
        ),
    ]
    session.add_all(rows)
    session.commit()


def test_aggregate_window_returns_stats():
    Session = setup_session()
    now = datetime(2025, 11, 22, 12, 0, tzinfo=timezone.utc)
    with Session() as session:
        seed_data(session, now)
        payload = aggregate_window(session, tag="reactor_temperature", window_minutes=60, reference_ts=now)
    assert payload["avg"] == 85.0
    assert payload["minimum"] == 80.0
    assert payload["maximum"] == 90.0
    assert payload["latest_value"] == 90.0
    assert payload["latest_ts"] == now - timedelta(minutes=5)
    assert payload["total_points"] == 2
