# Ingestion Service

Consumes simulator streams, enriches records with metadata, and writes them to TimescaleDB hypertables.

## TODO

- `consumer.py`: Subscribe to Mosquitto topics and fan out to processing pipelines.
- `writers/timescale.py`: Batch insert measurements with COPY, enforce retention policies.
- `schemas/`: Shared message and table schemas.
