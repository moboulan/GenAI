from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_URL = f"sqlite:///{(BASE_DIR / 'rag.db').as_posix()}"


class Settings(BaseSettings):
    database_url: str = Field(default=DEFAULT_DB_URL)
    chunk_size: int = Field(default=800, gt=100)
    chunk_overlap: int = Field(default=200, ge=0, lt=800)
    embedding_backend: str = Field(default="auto")
    embedding_dim: int = Field(default=384, gt=32)
    max_search_results: int = Field(default=5, gt=0)

    model_config = {
        "env_prefix": "RAG_",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
