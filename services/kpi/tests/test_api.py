from fastapi.testclient import TestClient

from app.api import app, get_service


class FakeKpiService:
    def __init__(self, payload):
        self._payload = payload

    def kpi(self, *, tag: str, window_minutes: int):  # pylint: disable=unused-argument
        return self._payload


client = TestClient(app)


def test_kpi_endpoint_returns_payload():
    payload = {
        "tag": "reactor_temperature",
        "window_minutes": 60,
        "start_ts": "2025-11-22T11:00:00Z",
        "end_ts": "2025-11-22T12:00:00Z",
        "avg": 10.0,
        "minimum": 5.0,
        "maximum": 15.0,
        "latest_value": 15.0,
        "latest_ts": "2025-11-22T12:00:00Z",
        "total_points": 2,
    }
    app.dependency_overrides[get_service] = lambda: FakeKpiService(payload)

    response = client.get("/kpi", params={"tag": "reactor_temperature"})
    assert response.status_code == 200
    assert response.json() == payload

    app.dependency_overrides.clear()


def test_kpi_endpoint_returns_404_when_no_data():
    payload = {
        "tag": "reactor_temperature",
        "window_minutes": 60,
        "start_ts": "2025-11-22T11:00:00Z",
        "end_ts": "2025-11-22T12:00:00Z",
        "avg": None,
        "minimum": None,
        "maximum": None,
        "latest_value": None,
        "latest_ts": None,
        "total_points": 0,
    }
    app.dependency_overrides[get_service] = lambda: FakeKpiService(payload)

    response = client.get("/kpi", params={"tag": "reactor_temperature"})
    assert response.status_code == 404
    assert response.json()["detail"] == "No data for tag reactor_temperature"

    app.dependency_overrides.clear()
