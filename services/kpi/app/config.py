from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_FORMULA_PATH = BASE_DIR / "formulas" / "definitions.yaml"


class Settings(BaseSettings):
    timescale_dsn: str = "postgresql+psycopg://tsp:tsp_pass@localhost:5432/tsp"
    formulas_path: Path = Field(default=DEFAULT_FORMULA_PATH)

    model_config = {
        "env_prefix": "KPI_",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
