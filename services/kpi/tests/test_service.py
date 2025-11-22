from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.formulas import FormulaDataUnavailable, FormulaRegistry
from app.models import Base, Measurement
from app.service import KpiService

FORMULA_PATH = Path(__file__).resolve().parents[1] / "app" / "formulas" / "definitions.yaml"


def build_service():
	engine = create_engine("sqlite:///:memory:", future=True)
	Base.metadata.create_all(engine)
	SessionLocal = sessionmaker(bind=engine, future=True)
	registry = FormulaRegistry.from_path(FORMULA_PATH)
	return KpiService(SessionLocal, registry), SessionLocal


def seed_measurements(session: Session, base_ts: datetime):
	rows = [
		Measurement(
			ts=base_ts - timedelta(minutes=idx * 5),
			tag="p2o5_concentration",
			topic="lab/p2o5",
			unit="pct",
			value=45.0 + idx,
		)
		for idx in range(1, 4)
	]
	rows.extend(
		Measurement(
			ts=base_ts - timedelta(minutes=idx * 5),
			tag="acid_flow",
			topic="process/acid/flow",
			unit="t_h",
			value=60.0 + idx,
		)
		for idx in range(1, 4)
	)
	rows.append(
		Measurement(
			ts=base_ts,
			tag="reactor_temperature",
			topic="process/reactor/temperature",
			unit="C",
			value=88.0,
		)
	)
	rows.append(
		Measurement(
			ts=base_ts,
			tag="free_acidity",
			topic="lab/free_acidity",
			unit="pct",
			value=1.4,
		)
	)
	session.add_all(rows)
	session.commit()


def test_evaluate_formula_returns_value():
	service, SessionLocal = build_service()
	now = datetime(2025, 11, 22, 12, 0, tzinfo=timezone.utc)
	with SessionLocal() as session:
		seed_measurements(session, now)

	result = service.evaluate_formula("rendement", window_minutes=60)
	assert result["name"] == "rendement"
	expected = ((46 + 47 + 48) / 3) / ((61 + 62 + 63) / 3) * 100
	assert result["value"] == pytest.approx(expected, rel=1e-6)
	assert set(result["inputs"].keys()) == {"p2o5_concentration", "acid_flow"}


def test_evaluate_formula_missing_tag_raises():
	service, _ = build_service()
	with pytest.raises(FormulaDataUnavailable):
		service.evaluate_formula("reactor_thermal_gap", window_minutes=15)
