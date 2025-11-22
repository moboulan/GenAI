# Orchestrator

Agent runtime responsible for intent detection, tool routing, rule evaluation, and response formatting.

## Structure

| Path | Purpose |
| --- | --- |
| `orchestrator/config.py` | Pydantic settings for downstream service URLs and defaults. |
| `orchestrator/agent.py` | Business logic that calls KPI/RAG tools and composes responses. |
| `orchestrator/clients.py` | Lightweight HTTP clients + deterministic LLM summarizer. |
| `orchestrator/rules/guardrails.yml` | Declarative safety notices and recommendation template. |
| `orchestrator/api.py` | FastAPI surface exposing `/chat` and `/health`. |
| `orchestrator/tests/` | Pytest suite for intent heuristics and API wiring. |

## Run Locally

```bash
cd orchestrator
/home/moboulan/Desktop/Industrial_Gen_AI/Code/.venv/bin/python -m uvicorn orchestrator.api:app --reload

# or via packaged entrypoint
/home/moboulan/Desktop/Industrial_Gen_AI/Code/.venv/bin/python -m orchestrator
```

Set `ORCH_RAG_BASE_URL`, `ORCH_KPI_BASE_URL`, and `ORCH_REQUEST_TIMEOUT` to point at the live services.
