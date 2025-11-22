from ingestion.consumer import parse_payloads


def test_parse_payloads_returns_measurements():
    messages = [
        '{"tag": "reactor_temperature", "topic": "process/reactor/temperature", "unit": "C", "value": 82.1, "ts": "2025-11-22T08:00:00+00:00"}'
    ]
    measurements = parse_payloads(messages)
    assert len(measurements) == 1
    assert measurements[0].tag == "reactor_temperature"
