from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


@dataclass
class Settings:
    mqtt_host: str = "127.0.0.1"
    mqtt_port: int = 1883
    mqtt_topics: List[str] = None  # type: ignore
    timescale_dsn: str = "postgresql+psycopg://tsp:tsp_pass@localhost:5432/tsp"

    @classmethod
    def load(cls) -> "Settings":
        topics_raw = os.getenv("MQTT_TOPICS", "process/#,lab/#")
        topics = [item.strip() for item in topics_raw.split(",") if item.strip()]
        return cls(
            mqtt_host=os.getenv("MQTT_HOST", "127.0.0.1"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
            mqtt_topics=topics,
            timescale_dsn=os.getenv("TIMESCALE_DSN", cls.timescale_dsn),
        )
