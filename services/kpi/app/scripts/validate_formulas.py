from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.formulas import FormulaEvaluationError, FormulaRegistry
from app.models import Base
from app.service import KpiService

DEFAULT_FORMULA_PATH = Path(__file__).resolve().parents[1] / "formulas" / "definitions.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate KPI formulas against a TimescaleDB instance")
    parser.add_argument("--dsn", default="postgresql+psycopg://tsp:tsp_pass@localhost:5432/tsp", help="SQLAlchemy DSN for TimescaleDB")
    parser.add_argument("--formula", help="Single formula name to evaluate", default=None)
    parser.add_argument("--window", type=int, help="Override window minutes", default=None)
    parser.add_argument("--formulas-path", type=Path, default=DEFAULT_FORMULA_PATH, help="Path to formulas YAML")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args()


def main():
    args = parse_args()
    engine = create_engine(args.dsn, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    registry = FormulaRegistry.from_path(args.formulas_path)
    service = KpiService(SessionLocal, registry)

    targets = [args.formula] if args.formula else [definition.name for definition in registry.list()]

    results = {}
    for name in targets:
        try:
            results[name] = service.evaluate_formula(name, window_minutes=args.window)
        except FormulaEvaluationError as exc:
            results[name] = {"error": str(exc)}

    if args.pretty:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(json.dumps(results, default=str))


if __name__ == "__main__":
    main()
