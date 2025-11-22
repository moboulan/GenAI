# Infra Stack

Holds configuration for Docker Compose, observability, and supporting services.

## Included Components

- TimescaleDB (metrics + process data)
- pgvector (RAG index)
- Redis (caching + queues)
- Mosquitto (MQTT bus)
- Ollama (local LLM runtime)
- Prometheus + Grafana (observability)
- KPI API (FastAPI container)
- RAG API (FastAPI container with sqlite volume)
- Agent Orchestrator (FastAPI, depends on KPI/RAG)

## Usage

```bash
make up    # start containers
make down  # stop containers
make logs  # follow stack logs
```
