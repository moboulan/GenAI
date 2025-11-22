# Simulator Module

Synthetic data publisher responsible for replaying historical sensor and lab measurements as MQTT messages and for producing CSV backfill extracts destined for TimescaleDB.

## Layout

| Path | Purpose |
| --- | --- |
| `sim_core/` | Shared primitives (schema loader + signal generator). |
| `schemas/tags.yaml` | Source of truth for simulated tags, units, and limits. |
| `publisher.py` | CLI that streams batches to Mosquitto or logs them in dry-run mode. |
| `backfill.py` | CLI that emits CSV files suitable for bulk loading. |
| `tests/` | Pytest suite covering schema parsing and generator behavior. |

## Usage

Install local dependencies:

```bash
cd simulator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Dry-run the publisher (logs JSON payloads instead of publishing):

```bash
python publisher.py --dry-run --interval 2.0
```

Generate a CSV for Timescale backfill:

```bash
python backfill.py --rows 180 --interval 30 --output data/backfill.csv
```

## Tests

From the repository root:

```bash
pytest simulator/tests
```
