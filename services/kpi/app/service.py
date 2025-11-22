from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session, sessionmaker

from .formulas import (
    FormulaDataUnavailable,
    FormulaError,
    FormulaEvaluationError,
    FormulaRegistry,
    evaluate_expression,
    make_context,
)
from .repository import aggregate_window


class KpiService:
    def __init__(self, session_factory: sessionmaker[Session], registry: FormulaRegistry):
        self._session_factory = session_factory
        self._registry = registry

    def kpi(self, tag: str, window_minutes: int, reference_ts: datetime | None = None):
        with self._session_factory() as session:
            return aggregate_window(
                session,
                tag=tag,
                window_minutes=window_minutes,
                reference_ts=reference_ts,
            )

    def list_formulas(self) -> list[dict[str, Any]]:
        return [definition.metadata() for definition in self._registry.list()]

    def evaluate_formula(
        self,
        name: str,
        window_minutes: int | None = None,
        reference_ts: datetime | None = None,
    ) -> Dict[str, Any]:
        definition = self._registry.get(name)
        window = window_minutes or definition.default_window_minutes
        with self._session_factory() as session:
            inputs: dict[str, dict[str, Any]] = {}
            for tag in definition.required_tags:
                stats = aggregate_window(
                    session,
                    tag=tag,
                    window_minutes=window,
                    reference_ts=reference_ts,
                )
                if stats["total_points"] == 0:
                    raise FormulaDataUnavailable(definition.name, tag)
                inputs[tag] = stats

        context = make_context(inputs)
        try:
            value = float(evaluate_expression(definition.expression, context))
        except FormulaError:
            raise
        except ZeroDivisionError as exc:
            raise FormulaEvaluationError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise FormulaEvaluationError(str(exc)) from exc

        return {
            "name": definition.name,
            "label": definition.label,
            "unit": definition.unit,
            "description": definition.description,
            "expression": definition.expression,
            "window_minutes": window,
            "value": value,
            "inputs": inputs,
        }
