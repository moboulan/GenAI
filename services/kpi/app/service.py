from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal

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


class WindowEmptyError(RuntimeError):
    pass


class KpiService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        registry: FormulaRegistry,
        anomaly_threshold: float = 2.5,
    ):
        self._session_factory = session_factory
        self._registry = registry
        self._anomaly_threshold = anomaly_threshold

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

    def trend(
        self,
        tag: str,
        window_minutes: int,
        reference_ts: datetime | None = None,
    ) -> Dict[str, Any]:
        stats = self.kpi(tag=tag, window_minutes=window_minutes, reference_ts=reference_ts)
        if stats["total_points"] < 2 or stats["earliest_value"] is None or stats["latest_value"] is None:
            raise WindowEmptyError(f"Not enough data for tag {tag}")
        earliest_ts = stats["earliest_ts"] or stats["start_ts"]
        latest_ts = stats["latest_ts"] or stats["end_ts"]
        elapsed_minutes = max((latest_ts - earliest_ts).total_seconds() / 60, 1e-9)
        delta = stats["latest_value"] - stats["earliest_value"]
        slope = delta / elapsed_minutes
        percent_change = None
        if stats["earliest_value"] not in (None, 0):
            percent_change = (delta / stats["earliest_value"]) * 100

        tolerance = max(abs(stats["earliest_value"]) * 0.005, 0.01)
        direction: Literal["up", "down", "flat"] = "flat"
        if delta > tolerance:
            direction = "up"
        elif delta < -tolerance:
            direction = "down"

        return {
            "tag": tag,
            "window_minutes": window_minutes,
            "start_ts": stats["start_ts"],
            "end_ts": stats["end_ts"],
            "earliest_value": stats["earliest_value"],
            "earliest_ts": earliest_ts,
            "latest_value": stats["latest_value"],
            "latest_ts": latest_ts,
            "delta": delta,
            "slope_per_min": slope,
            "percent_change": percent_change,
            "direction": direction,
        }

    def anomaly(
        self,
        tag: str,
        window_minutes: int,
        reference_ts: datetime | None = None,
        threshold: float | None = None,
    ) -> Dict[str, Any]:
        stats = self.kpi(tag=tag, window_minutes=window_minutes, reference_ts=reference_ts)
        latest_value = stats["latest_value"]
        avg = stats["avg"]
        stddev = stats["stddev"]
        if stats["total_points"] < 2 or latest_value is None or avg is None or stddev in (None, 0):
            raise WindowEmptyError(f"Not enough data for tag {tag}")
        z_score = (latest_value - avg) / stddev
        threshold_value = threshold or self._anomaly_threshold
        is_anomaly = abs(z_score) >= threshold_value
        return {
            "tag": tag,
            "window_minutes": window_minutes,
            "start_ts": stats["start_ts"],
            "end_ts": stats["end_ts"],
            "latest_value": latest_value,
            "latest_ts": stats["latest_ts"],
            "avg": avg,
            "stddev": stddev,
            "z_score": z_score,
            "threshold": threshold_value,
            "is_anomaly": bool(is_anomaly),
            "total_points": stats["total_points"],
        }
