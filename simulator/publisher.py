from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Iterable

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - optional dependency during tests
    mqtt = None

from simulator.sim_core.generator import SimSignalGenerator
from simulator.sim_core.schema import Tag, load_tags

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
LOGGER = logging.getLogger("simulator.publisher")


def publish_loop(tags: Iterable[Tag], host: str, port: int, interval: float, dry_run: bool) -> None:
    generator = SimSignalGenerator(tags)
    client = None
    if not dry_run:
        if mqtt is None:
            raise RuntimeError("paho-mqtt is required when not running in --dry-run mode")
        client = mqtt.Client()
        client.connect(host, port, keepalive=60)

    for batch in generator.stream(interval=interval):
        payloads = [obs.as_dict() for obs in batch]
        for obs in payloads:
            message = json.dumps(obs)
            if dry_run:
                LOGGER.info("preview %s", message)
            else:
                assert client is not None
                result = client.publish(obs["topic"], message, qos=0, retain=False)
                result.wait_for_publish()
        if not dry_run and client is not None:
            client.loop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulated MQTT publisher for TSP plant data")
    parser.add_argument("--config", default="schemas/tags.yaml", help="Path to tag definition file")
    parser.add_argument("--host", default="127.0.0.1", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between batches")
    parser.add_argument("--dry-run", action="store_true", help="Log messages instead of publishing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tags = load_tags(Path(__file__).parent / args.config)
    publish_loop(tags, host=args.host, port=args.port, interval=args.interval, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
