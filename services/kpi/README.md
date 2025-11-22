# KPI Service

FastAPI microservice exposing KPI, trend, and anomaly endpoints backed by TimescaleDB.

## TODO

- `app/main.py`: FastAPI application skeleton with health checks.
- `kpi/formulas/`: YAML definitions parsed at startup.
- `tests/`: Pytest suite covering formula correctness and regression windows.
