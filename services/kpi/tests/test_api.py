from fastapi.testclient import TestClient

from app.api import app, get_service
from app.formulas import FormulaDataUnavailable, FormulaEvaluationError
from app.service import WindowEmptyError


class FakeKpiService:
    def __init__(self, payload):
        self._payload = payload

    def kpi(self, *, tag: str, window_minutes: int):  # pylint: disable=unused-argument
        return self._payload


class FakeAnalyticsService(FakeKpiService):
    def __init__(self, payload, trend_payload=None, anomaly_payload=None, trend_error=None, anomaly_error=None):
        super().__init__(payload)
        self._trend_payload = trend_payload
        self._anomaly_payload = anomaly_payload
        self._trend_error = trend_error
        self._anomaly_error = anomaly_error

    def trend(self, *, tag: str, window_minutes: int):  # pylint: disable=unused-argument
        if self._trend_error:
            raise self._trend_error
        return self._trend_payload

    def anomaly(self, *, tag: str, window_minutes: int, threshold=None):  # pylint: disable=unused-argument
        if self._anomaly_error:
            raise self._anomaly_error
        if threshold is not None and self._anomaly_payload:
            payload = dict(self._anomaly_payload)
            payload["threshold"] = threshold
            return payload
        return self._anomaly_payload


class FakeFormulaService:
    def __init__(self, metadata=None, result=None, error=None):
        self._metadata = metadata or []
        self._result = result
        self._error = error

    def list_formulas(self):
        return self._metadata

    def evaluate_formula(self, name: str, window_minutes: int | None = None):  # pylint: disable=unused-argument
        if self._error:
            raise self._error
        return self._result


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
        "earliest_value": 5.0,
        "earliest_ts": "2025-11-22T11:30:00Z",
        "stddev": 1.5,
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
        "earliest_value": None,
        "earliest_ts": None,
        "stddev": None,
        "total_points": 0,
    }
    app.dependency_overrides[get_service] = lambda: FakeKpiService(payload)

    response = client.get("/kpi", params={"tag": "reactor_temperature"})
    assert response.status_code == 404
    assert response.json()["detail"] == "No data for tag reactor_temperature"

    app.dependency_overrides.clear()


def test_list_formulas_returns_metadata():
    metadata = [
        {
            "name": "rendement",
            "label": "Rendement P2O5",
            "unit": "pct",
            "description": "",
            "default_window_minutes": 30,
            "required_tags": ["p2o5_concentration", "acid_flow"],
        }
    ]
    app.dependency_overrides[get_service] = lambda: FakeFormulaService(metadata=metadata)

    response = client.get("/kpi/formulas")
    assert response.status_code == 200
    assert response.json() == metadata

    app.dependency_overrides.clear()


def test_evaluate_formula_returns_value():
    result = {
        "name": "rendement",
        "label": "Rendement P2O5",
        "unit": "pct",
        "description": "",
        "expression": "(p2o5_concentration.avg / acid_flow.avg) * 100",
        "window_minutes": 30,
        "value": 92.5,
        "inputs": {
            "p2o5_concentration": {
                "tag": "p2o5_concentration",
                "window_minutes": 30,
                "start_ts": "2025-11-22T11:30:00Z",
                "end_ts": "2025-11-22T12:00:00Z",
                "avg": 45.0,
                "minimum": 44.0,
                "maximum": 46.0,
                "latest_value": 45.5,
                "latest_ts": "2025-11-22T12:00:00Z",
                "earliest_value": 44.0,
                "earliest_ts": "2025-11-22T11:30:00Z",
                "stddev": 0.4,
                "total_points": 8,
            },
            "acid_flow": {
                "tag": "acid_flow",
                "window_minutes": 30,
                "start_ts": "2025-11-22T11:30:00Z",
                "end_ts": "2025-11-22T12:00:00Z",
                "avg": 48.65,
                "minimum": 47.8,
                "maximum": 49.3,
                "latest_value": 48.9,
                "latest_ts": "2025-11-22T12:00:00Z",
                "earliest_value": 47.8,
                "earliest_ts": "2025-11-22T11:30:00Z",
                "stddev": 0.6,
                "total_points": 8,
            },
        },
    }
    app.dependency_overrides[get_service] = lambda: FakeFormulaService(result=result)

    response = client.get("/kpi/formulas/rendement")
    assert response.status_code == 200
    assert response.json() == result

    app.dependency_overrides.clear()


def test_evaluate_formula_handles_missing_data():
    service = FakeFormulaService(error=FormulaDataUnavailable("rendement", "acid_flow"))
    app.dependency_overrides[get_service] = lambda: service

    response = client.get("/kpi/formulas/rendement")
    assert response.status_code == 404
    assert "No data" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_evaluate_formula_handles_invalid_window_param():
    app.dependency_overrides[get_service] = lambda: FakeFormulaService()

    response = client.get("/kpi/formulas/rendement", params={"window_minutes": 0})
    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_evaluate_formula_handles_expression_error():
    service = FakeFormulaService(error=FormulaEvaluationError("boom"))
    app.dependency_overrides[get_service] = lambda: service

    response = client.get("/kpi/formulas/rendement")
    assert response.status_code == 422
    assert response.json()["detail"] == "boom"

    app.dependency_overrides.clear()


def test_trend_endpoint_returns_payload():
    payload = {
        "tag": "reactor_temperature",
        "window_minutes": 30,
        "start_ts": "2025-11-22T11:30:00Z",
        "end_ts": "2025-11-22T12:00:00Z",
        "earliest_value": 80.0,
        "earliest_ts": "2025-11-22T11:30:00Z",
        "latest_value": 90.0,
        "latest_ts": "2025-11-22T12:00:00Z",
        "delta": 10.0,
        "slope_per_min": 0.3333,
        "percent_change": 12.5,
        "direction": "up",
    }
    service = FakeAnalyticsService(payload, trend_payload=payload)
    app.dependency_overrides[get_service] = lambda: service

    response = client.get("/kpi/trend", params={"tag": "reactor_temperature"})
    assert response.status_code == 200
    assert response.json() == payload

    app.dependency_overrides.clear()


def test_trend_endpoint_handles_missing_data():
    service = FakeAnalyticsService({}, trend_error=WindowEmptyError("no data"))
    app.dependency_overrides[get_service] = lambda: service

    response = client.get("/kpi/trend", params={"tag": "reactor_temperature"})
    assert response.status_code == 404
    assert "no data" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_anomaly_endpoint_returns_payload_and_supports_override():
    anomaly_payload = {
        "tag": "reactor_temperature",
        "window_minutes": 30,
        "start_ts": "2025-11-22T11:30:00Z",
        "end_ts": "2025-11-22T12:00:00Z",
        "latest_value": 95.0,
        "latest_ts": "2025-11-22T12:00:00Z",
        "avg": 85.0,
        "stddev": 4.0,
        "z_score": 2.5,
        "threshold": 2.5,
        "is_anomaly": True,
        "total_points": 24,
    }
    service = FakeAnalyticsService(anomaly_payload, anomaly_payload=anomaly_payload)
    app.dependency_overrides[get_service] = lambda: service

    response = client.get("/kpi/anomaly", params={"tag": "reactor_temperature", "threshold": 3.0})
    assert response.status_code == 200
    body = response.json()
    assert body["threshold"] == 3.0
    assert body["latest_value"] == 95.0

    app.dependency_overrides.clear()


def test_anomaly_endpoint_handles_missing_data():
    service = FakeAnalyticsService({}, anomaly_error=WindowEmptyError("not enough"))
    app.dependency_overrides[get_service] = lambda: service

    response = client.get("/kpi/anomaly", params={"tag": "reactor_temperature"})
    assert response.status_code == 404
    assert "not enough" in response.json()["detail"]

    app.dependency_overrides.clear()
