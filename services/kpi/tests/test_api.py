from fastapi.testclient import TestClient

from app.api import app, get_service
from app.formulas import FormulaDataUnavailable, FormulaEvaluationError


class FakeKpiService:
    def __init__(self, payload):
        self._payload = payload

    def kpi(self, *, tag: str, window_minutes: int):  # pylint: disable=unused-argument
        return self._payload


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
