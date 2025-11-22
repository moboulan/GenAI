# Simulator Module

Responsible for replaying historical sensor and lab data as MQTT/Redis streams and writing snapshots to TimescaleDB.

## TODO

- `publisher.py`: Stream CSV/Parquet rows to Mosquitto topics per equipment.
- `backfill.py`: Bulk insert historical windows into TimescaleDB hypertables.
- `schemas/`: YAML files describing tag metadata, engineering units, and sampling cadence.
