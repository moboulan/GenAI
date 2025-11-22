from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from .repository import aggregate_window


class KpiService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def kpi(self, tag: str, window_minutes: int):
        with self._session_factory() as session:
            return aggregate_window(session, tag=tag, window_minutes=window_minutes)
