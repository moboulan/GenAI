from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import get_settings
from .models import Base
from .schemas import KpiResponse
from .service import KpiService

app = FastAPI(title="KPI Service")


def get_service() -> KpiService:
    settings = get_settings()
    engine = create_engine(settings.timescale_dsn, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    return KpiService(SessionLocal)


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
