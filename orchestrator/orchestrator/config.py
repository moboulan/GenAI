from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    rag_base_url: str = Field(default="http://localhost:8002")
    kpi_base_url: str = Field(default="http://localhost:8001")
    llm_model_name: str = Field(default="local-scribe")
    max_rag_hits: int = Field(default=4, gt=0)
    response_language: str = Field(default="fr")
    request_timeout: float = Field(default=5.0, gt=0)

    model_config = {
        "env_prefix": "ORCH_",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
