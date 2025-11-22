# Run Book

End-to-end steps for launching the TSP Copilot stack locally.

## 1. Prerequisites

- Docker + docker compose plugin
- Node.js 18+ and npm (for the UI)
- Python 3.11 environment (repo already has `.venv`)

## 2. Start Infrastructure + Containerized Services

```bash
cd implementation
make services-build
```

This builds and starts TimescaleDB, pgvector, Redis, Mosquitto, Ollama, Prometheus, Grafana, KPI, and Orchestrator containers. (RAG now runs directly on the host to avoid repeatedly downloading large PyTorch wheels.)

Health probes:

- KPI: <http://localhost:8001/health>
- RAG (host process): <http://localhost:8002/health>
- Orchestrator: <http://localhost:8010/health>

## 3. Start the RAG Service Locally

Open a second terminal (so the server can keep running) and execute:

```bash
cd implementation
make rag-install   # first run only; installs requirements into your active Python env/venv
make rag-serve     # blocks and serves FastAPI on http://localhost:8002
```

> Tip: using the repo's `.venv` (`source ../.venv/bin/activate`) keeps dependencies sandboxed. The orchestrator container connects to `http://host.docker.internal:8002`, so expose on all interfaces (the make target already does).

## 4. Seed KPI Data (optional)

```bash
make seed
```

Runs `app.scripts.seed_timescale` to load deterministic measurements into TimescaleDB.

## 5. (Optional) Rebuild RAG Index

```bash
cd services/rag
/home/moboulan/Desktop/Industrial_Gen_AI/Code/.venv/bin/python -m scripts.cli ingest ../../Docs\ TSP --metadata phase=sechage
```

Adjust paths/metadata as needed; the CLI prints document IDs that were upserted.

## 6. Launch the Web UI

```bash
cd implementation
make ui-dev
```

- Installs npm dependencies (first run) and starts the Vite dev server on <http://localhost:5173>.
- The default `VITE_ORCH_BASE_URL` points to `<http://localhost:8010>`; override via `.env` if needed.

## 7. Interact

- Use the web UI chat to query KPIs or request procedures.
- For direct API calls, POST to `<http://localhost:8010/chat>` with `{"message": "rendement"}`.

## 8. Shutdown

```bash
make services-stop   # stop app containers
make down            # tear down entire compose stack (or `docker compose down -v` to drop volumes)
```

## 9. Troubleshooting

- `make logs` to tail all compose logs.
- `make ps` to ensure containers are healthy.
- Run pytest per service (`cd services/kpi && /path/to/python -m pytest`) if APIs misbehave.
