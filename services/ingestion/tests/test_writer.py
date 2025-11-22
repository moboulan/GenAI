from datetime import datetime, timezone

from sqlalchemy import create_engine, text

from ingestion.models import Measurement
from ingestion.writer import TimescaleWriter


def test_writer_inserts_rows(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    writer = TimescaleWriter(engine)
    measurement = Measurement(
        tag="reactor_temperature",
        topic="process/reactor/temperature",
        unit="C",
        value=83.5,
        timestamp=datetime(2025, 11, 22, 9, 30, tzinfo=timezone.utc),
    )
    writer.write([measurement])
    with engine.connect() as conn:
        result = conn.execute(text("SELECT tag, value FROM measurements"))
        row = result.first()
        assert row is not None
        assert row.tag == "reactor_temperature"
        assert abs(row.value - 83.5) < 1e-6
