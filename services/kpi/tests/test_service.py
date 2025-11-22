from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.formulas import FormulaDataUnavailable, FormulaRegistry
from app.models import Base, Measurement
from app.service import KpiService, WindowEmptyError

FORMULA_PATH = Path(__file__).resolve().parents[1] / "app" / "formulas" / "definitions.yaml"
P2O5_VALUES = (45.0, 46.0, 47.0, 48.0)
ACID_FLOW_VALUES = (60.0, 61.0, 62.0, 63.0)


def build_service():
	engine = create_engine("sqlite:///:memory:", future=True)
	Base.metadata.create_all(engine)
	SessionLocal = sessionmaker(bind=engine, future=True)
	registry = FormulaRegistry.from_path(FORMULA_PATH)
	return KpiService(SessionLocal, registry), SessionLocal


def seed_measurements(session: Session, base_ts: datetime):
	rows = []
	for idx, value in enumerate(P2O5_VALUES, start=1):
		rows.append(
			Measurement(
				ts=base_ts - timedelta(minutes=idx * 5),
				tag="p2o5_concentration",
				topic="lab/p2o5",
				unit="pct",
				value=value,
			)
		)
	for idx, value in enumerate(ACID_FLOW_VALUES, start=1):
		rows.append(
			Measurement(
				ts=base_ts - timedelta(minutes=idx * 5),
				tag="acid_flow",
				topic="process/acid/flow",
				unit="t_h",
				value=value,
			)
		)
	reactor_values = (95.0, 93.0, 91.0, 89.0, 87.0, 85.0)
	for idx, value in enumerate(reactor_values):
		rows.append(
			Measurement(
				ts=base_ts - timedelta(minutes=idx * 5),
				tag="reactor_temperature",
				topic="process/reactor/temperature",
				unit="C",
				value=value,
			)
		)
	acidity_values = (1.6, 1.55, 1.5, 1.45, 1.4)
	for idx, value in enumerate(acidity_values):
		rows.append(
			Measurement(
				ts=base_ts - timedelta(minutes=idx * 10),
				tag="free_acidity",
				topic="lab/free_acidity",
				unit="pct",
				value=value,
			)
		)
	session.add_all(rows)
	session.commit()


def test_evaluate_formula_returns_value():
	service, SessionLocal = build_service()
	now = datetime(2025, 11, 22, 12, 0, tzinfo=timezone.utc)
	with SessionLocal() as session:
		seed_measurements(session, now)

	result = service.evaluate_formula("rendement", window_minutes=60, reference_ts=now)
	assert result["name"] == "rendement"
	expected = (sum(P2O5_VALUES) / len(P2O5_VALUES)) / (sum(ACID_FLOW_VALUES) / len(ACID_FLOW_VALUES)) * 100
	assert result["value"] == pytest.approx(expected, rel=1e-6)
	assert set(result["inputs"].keys()) == {"p2o5_concentration", "acid_flow"}


def test_evaluate_formula_missing_tag_raises():
	service, _ = build_service()
	with pytest.raises(FormulaDataUnavailable):
		service.evaluate_formula("recycle_ratio_alert", window_minutes=30)


def test_reactor_gap_formula_uses_latest_value():
	service, SessionLocal = build_service()
	now = datetime(2025, 11, 22, 12, 0, tzinfo=timezone.utc)
	with SessionLocal() as session:
		seed_measurements(session, now)

	result = service.evaluate_formula("reactor_thermal_gap", window_minutes=15, reference_ts=now)
	assert result["value"] == pytest.approx(95.0 - 85.0)


def test_trend_computation_highlights_direction():
	service, SessionLocal = build_service()
	now = datetime(2025, 11, 22, 12, 0, tzinfo=timezone.utc)
	with SessionLocal() as session:
		seed_measurements(session, now)

	payload = service.trend("reactor_temperature", window_minutes=60, reference_ts=now)
	assert payload["direction"] == "up"
	assert payload["delta"] > 0
	assert payload["earliest_value"] < payload["latest_value"]


def test_anomaly_flags_large_z_score():
	service, SessionLocal = build_service()
	now = datetime(2025, 11, 22, 12, 0, tzinfo=timezone.utc)
	with SessionLocal() as session:
		seed_measurements(session, now)

	payload = service.anomaly("reactor_temperature", window_minutes=60, threshold=1.0, reference_ts=now)
	assert payload["is_anomaly"] is True
	assert payload["z_score"] >= 1.0


def test_anomaly_raises_when_no_data():
	service, _ = build_service()
	with pytest.raises(WindowEmptyError):
		service.anomaly("unknown", window_minutes=30)
