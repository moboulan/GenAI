from __future__ import annotations

import json
import logging
from typing import Iterable, List

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    mqtt = None

from .models import Measurement
from .writer import TimescaleWriter, decode_batch

LOGGER = logging.getLogger("ingestion.consumer")


def _ensure_client():
    if mqtt is None:
        raise RuntimeError("paho-mqtt not installed; install services/ingestion requirements")
    return mqtt.Client()


class MqttIngestionService:
    def __init__(self, broker_host: str, broker_port: int, topics: Iterable[str], writer: TimescaleWriter):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topics = list(topics)
        self.writer = writer
        self.client = _ensure_client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):  # pragma: no cover
        LOGGER.info("Connected to MQTT broker (%s)", reason_code)
        for topic in self.topics:
            client.subscribe(topic)

    def _on_message(self, client, userdata, msg):  # pragma: no cover
        try:
            payload = json.loads(msg.payload)
            measurement = Measurement.from_payload(payload)
            self.writer.write([measurement])
        except Exception:  # noqa: BLE001
            LOGGER.exception("Failed to process message on topic %s", msg.topic)

    def start(self):  # pragma: no cover
        self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        self.client.loop_forever()


def parse_payloads(messages: Iterable[str]) -> List[Measurement]:
    decoded = [json.loads(msg) for msg in messages]
    return decode_batch(decoded)
