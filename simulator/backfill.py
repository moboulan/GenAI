from __future__ import annotations

import argparse
import csv
from argparse import Namespace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from simulator.sim_core.generator import SimSignalGenerator
from simulator.sim_core.schema import load_tags


def generate_rows(rows: int, interval: float, generator: SimSignalGenerator):
    current_ts = datetime.now(timezone.utc) - timedelta(seconds=rows * interval)
    for _ in range(rows):
        batch = generator.next_batch()
        for obs in batch:
            yield {
                "timestamp": current_ts.isoformat(),
                "tag": obs.tag.name,
                "topic": obs.tag.topic,
                "unit": obs.tag.unit,
                "value": obs.value,
            }
        current_ts += timedelta(seconds=interval)


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser(description="Generate CSV suitable for TimescaleDB backfill")
    parser.add_argument("--config", default="schemas/tags.yaml", help="Path to tag definition file")
    parser.add_argument("--rows", type=int, default=120, help="Number of time steps to generate")
    parser.add_argument("--interval", type=float, default=60.0, help="Seconds between rows")
    parser.add_argument("--output", default="data/backfill.csv", help="Output CSV path")
    args = parser.parse_args()
    return args


def main() -> None:
    args = parse_args()
    tags = load_tags(Path(__file__).parent / args.config)
    generator = SimSignalGenerator(tags)
    output_path = Path(__file__).parent / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["timestamp", "tag", "topic", "unit", "value"])
        writer.writeheader()
        for row in generate_rows(args.rows, args.interval, generator):
            writer.writerow(row)


if __name__ == "__main__":
    main()
