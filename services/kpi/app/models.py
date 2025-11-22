from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, Float


class Base(DeclarativeBase):
    pass


class Measurement(Base):
    __tablename__ = "measurements"

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    tag: Mapped[str] = mapped_column(String, primary_key=True)
    topic: Mapped[str] = mapped_column(String)
    unit: Mapped[str] = mapped_column(String)
    value: Mapped[float] = mapped_column(Float)
