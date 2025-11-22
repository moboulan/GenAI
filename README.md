# TSP Copilot Implementation Repo

This repository hosts the modular implementation of the fully local TSP conversational copilot described in `plan.md`. Each directory maps to a service in the architecture so components can be iterated and validated independently before end-to-end integration.

## Repository Structure

| Path | Purpose |
| --- | --- |
| `simulator/` | Data generator and replay utilities for sensor and lab streams. |
| `services/ingestion/` | Connectors that subscribe to simulator streams and persist measurements into TimescaleDB. |
| `services/kpi/` | FastAPI microservice exposing KPI/anomaly endpoints calculated from TimescaleDB. |
| `services/rag/` | Document ingestion, chunking, and vector-store APIs. |
| `orchestrator/` | Agent runtime (LangChain/Semantic Kernel) coordinating tools + local LLM. |
| `ui/` | React/Vite chat interface plus local API gateway. |
| `infra/` | Docker Compose stack, Makefile helpers, and ops scripts. |
| `docs/` | Design notes, runbooks, and evaluation reports. |

## Step-by-Step Build Order

1. **Infra bootstrap** (`infra/`)
   - Compose stack for TimescaleDB, pgvector, Redis, Mosquitto, Ollama, Prometheus, Grafana.
   - Shared `.env` and Make targets (`make up`, `make down`, `make logs`).
2. **Data foundation** (`simulator/`, `services/ingestion/`)
   - Replay historical CSV/Parquet, publish to Mosquitto/Redis Streams, mirror into TimescaleDB hypertables.
   - Provide schema definitions under `services/ingestion/schemas/`.
3. **KPI + anomaly API** (`services/kpi/`)
   - FastAPI service reading KPI formulas from versioned YAML, computing rolling windows, pushing alerts.
4. **Knowledge base + RAG** (`services/rag/`)
   - CLI for DOCX/PPTX/PDF extraction, metadata tagging, and pgvector ingestion.
   - HTTP API exposing `/search` + `/upsert` endpoints.
5. **Rules + orchestrator** (`orchestrator/`)
   - YAML decision trees compiled into guards, tool wiring, prompt templates enforcing citations and safety context.
6. **UI + scenario runner** (`ui/` + `docs/`)
   - Chat interface with streaming SSE, inline charts, scenario scripting harness for demos.

## Getting Started

```bash
cd infra
make up         # spin up databases, message bus, LLM server
make seed       # (todo) load sample data, create tables, install embeddings
```

Each module includes its own README with setup notes, TODOs, and test commands. Follow the order above to bring the system online incrementally.
