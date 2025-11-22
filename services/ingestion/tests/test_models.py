from datetime import datetime, timezone

from ingestion.models import Measurement


def test_measurement_from_payload_parses_timestamp():
    payload = {
        "tag": "reactor_temperature",
        "topic": "process/reactor/temperature",
        "unit": "C",
        "value": 84.2,
        "ts": "2025-11-22T10:00:00+00:00",
    }
    measurement = Measurement.from_payload(payload)
    assert measurement.timestamp == datetime(2025, 11, 22, 10, 0, tzinfo=timezone.utc)
    assert measurement.value == 84.2
