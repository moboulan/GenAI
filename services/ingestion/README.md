# Ingestion Service

Consumes MQTT messages emitted by the simulator and persists them into TimescaleDB (or any Postgres-compatible database) using SQLAlchemy. Includes a small config loader plus unit tests so the service can be validated without a running broker/DB.

## Layout

| Path | Purpose |
| --- | --- |
| `ingestion/models.py` | Measurement dataclass + timestamp parsing helpers. |
| `ingestion/writer.py` | SQLAlchemy table definition and writer abstraction. |
| `ingestion/consumer.py` | MQTT consumer that converts JSON payloads into measurements. |
| `ingestion/config.py` | Environment-driven settings. |
| `main.py` | Entry script wiring config + consumer. |
| `tests/` | Pytest suite for models, writer, and payload parsing. |

## Setup

```bash
cd services/ingestion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Running (local stack)

```bash
export TIMESCALE_DSN="postgresql+psycopg://tsp:tsp_pass@localhost:5432/tsp"
export MQTT_TOPICS="process/#,lab/#"
python main.py
```

## Tests

```bash
cd /home/moboulan/Desktop/Industrial_Gen_AI/Code/implementation
pytest services/ingestion/tests
```
