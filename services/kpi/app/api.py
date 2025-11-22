from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .formulas import FormulaDataUnavailable, FormulaEvaluationError, FormulaNotFound, FormulaRegistry
from .models import Base
from .schemas import AnomalyResponse, FormulaComputation, FormulaMetadata, KpiResponse, TrendResponse
from .service import KpiService, WindowEmptyError

app = FastAPI(title="KPI Service")


@lru_cache(maxsize=1)
def _get_session_factory() -> sessionmaker[Session]:
    settings = get_settings()
    engine = create_engine(settings.timescale_dsn, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)


@lru_cache(maxsize=1)
def _get_formula_registry() -> FormulaRegistry:
    settings = get_settings()
    return FormulaRegistry.from_path(settings.formulas_path)


def get_service() -> KpiService:
    settings = get_settings()
    return KpiService(
        _get_session_factory(),
        _get_formula_registry(),
        anomaly_threshold=settings.anomaly_z_threshold,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/kpi", response_model=KpiResponse)
def get_kpi(tag: str, window_minutes: int = 30, service: KpiService = Depends(get_service)) -> KpiResponse:
    if window_minutes <= 0:
        raise HTTPException(status_code=422, detail="window_minutes must be positive")
    payload = service.kpi(tag=tag, window_minutes=window_minutes)
    if payload["avg"] is None:
        raise HTTPException(status_code=404, detail=f"No data for tag {tag}")
    return KpiResponse(**payload)


@app.get("/kpi/formulas", response_model=list[FormulaMetadata])
def list_formulas(service: KpiService = Depends(get_service)) -> list[FormulaMetadata]:
    return service.list_formulas()


@app.get("/kpi/formulas/{name}", response_model=FormulaComputation)
def evaluate_formula(
    name: str,
    window_minutes: int | None = None,
    service: KpiService = Depends(get_service),
) -> FormulaComputation:
    if window_minutes is not None and window_minutes <= 0:
        raise HTTPException(status_code=422, detail="window_minutes must be positive")
    try:
        return service.evaluate_formula(name=name, window_minutes=window_minutes)
    except FormulaNotFound as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FormulaDataUnavailable as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FormulaEvaluationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/kpi/trend", response_model=TrendResponse)
def get_trend(tag: str, window_minutes: int = 30, service: KpiService = Depends(get_service)) -> TrendResponse:
    if window_minutes <= 0:
        raise HTTPException(status_code=422, detail="window_minutes must be positive")
    try:
        return TrendResponse(**service.trend(tag=tag, window_minutes=window_minutes))
    except WindowEmptyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/kpi/anomaly", response_model=AnomalyResponse)
def get_anomaly(
    tag: str,
    window_minutes: int = 30,
    threshold: float | None = None,
    service: KpiService = Depends(get_service),
) -> AnomalyResponse:
    if window_minutes <= 0:
        raise HTTPException(status_code=422, detail="window_minutes must be positive")
    try:
        return AnomalyResponse(**service.anomaly(tag=tag, window_minutes=window_minutes, threshold=threshold))
    except WindowEmptyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
