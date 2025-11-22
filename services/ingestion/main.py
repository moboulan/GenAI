from __future__ import annotations

from ingestion.config import Settings
from ingestion.consumer import MqttIngestionService
from ingestion.writer import TimescaleWriter


def main() -> None:  # pragma: no cover - orchestration
    settings = Settings.load()
    writer = TimescaleWriter(settings.timescale_dsn)
    service = MqttIngestionService(
        broker_host=settings.mqtt_host,
        broker_port=settings.mqtt_port,
        topics=settings.mqtt_topics,
        writer=writer,
    )
    service.start()


if __name__ == "__main__":
    main()
