from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    timescale_dsn: str = "postgresql+psycopg://tsp:tsp_pass@localhost:5432/tsp"

    model_config = {
        "env_prefix": "KPI_",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
