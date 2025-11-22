# Implementation Plan

## 1. Objectives

- Deliver a conversational copilot that can query simulated TSP process data, generate KPIs, cite procedures, and recommend safe corrective actions.
- Reuse the curated references in `Docs TSP/` (logigrammes, KPI workbook, training decks, quality report) to ground answers with verifiable citations.
- Demonstrate the flagship scenario ("Pourquoi le rendement baisse depuis 30 min ?") while building a reusable architecture for future industrial copilots.

## 2. Target Architecture (Fully Local)

```text
[Docs TSP sources]---(ETL)--->[Vector Store + Metadata]
       |                               ^
       |                               |
[Sensor/Lab Simulator]--(Stream)->[Time-Series DB]<-(API)->[KPI/Analytics Service]
                                           |
                                           v
                                [Agent Orchestrator]
                                       |
            ----------------------------------------------------
            | KPI Tool | Anomaly Tool | RAG Tool | Procedure Rules |
                                       |
                                  [Web Chat UI]
```

- **Data sources:** Simulated historian and lab batches plus static docs under `Docs TSP/`.
- **Ingestion & replay:** Python service that replays historical CSV/Parquet or synthetic data, publishes via WebSocket/REST or local MQTT, and persists to a local TimescaleDB (Postgres) container.
- **KPI & analytics service:** Containerized FastAPI (or Flask) running locally, exposing `/kpi`, `/anomaly`, `/trend` endpoints with formulas from `KPI  2025.xlsm` and latency budget under two seconds.
- **Knowledge base & RAG:** Local text extraction pipeline (python-docx, python-pptx, pdfminer) producing markdown chunks with metadata (process phase, equipment, KPI) indexed into a local pgvector or Weaviate container.
- **LLM inference:** Local Llama.cpp/Ollama server hosting an open model (Llama 3 8B, Mistral 7B, etc.) to avoid cloud dependencies.
- **Procedure rules:** Deterministic guardrails derived from `Logigramme process/*` encoded as JSON/YAML and executed in-process to constrain LLM output.
- **Agent orchestrator:** Local LangChain/Semantic Kernel runner that detects intent, calls KPI/anomaly/RAG/chart tools, merges rule outputs, and emits responses with impact/risques/prerequis tables plus citations.
- **Presentation layer:** Local web chat UI (React + Vite dev server) communicating with a Python/Node gateway; supports streaming responses, inline citations, chart widgets, and scenario playback harness.

### Local Stack Choices

- **Container orchestration:** Docker Compose with services for TimescaleDB, pgvector (or Weaviate), Redis (for caching), Ollama/llama.cpp server, and the KPI/API services.
- **Messaging:** Local MQTT (Eclipse Mosquitto) or Redis Streams for simulator-to-service communication.
- **Observability:** Grafana + Prometheus containers scraping local services.
- **Auth & secrets:** `.env` files managed locally; no external secret stores.

## 3. Step-by-Step Delivery Plan

1. **Setup & Discovery (Week 0)**
   - Catalogue every file in `Docs TSP/` and tag by process phase (reaction, granulation, sechage, ensachage).
   - Confirm required sensor tags and lab variables (P2O5 SE/SC, acidite libre, humidite, debit acide, temperature reacteur, taux recycle, rendement).
   - Initialize a mono-repo with `docker-compose.yml` scaffolding the local services (TimescaleDB, pgvector, Redis, Mosquitto, Ollama) and a `Makefile` for common commands.
   - Document hardware requirements (GPU/CPU, RAM, disk) needed to run the chosen local LLM and databases.
2. **Data Foundation (Week 1)**
   - Implement the sensor/lab data generator (Python) that replays CSV/Parquet and streams to Mosquitto/Redis Streams; mirror data into TimescaleDB using the `/write` API.
   - Containerize TimescaleDB with seed scripts that create measurement tables, hypertables, and retention policies; verify inserts via `psql`.
   - Transcribe KPI formulas from `KPI  2025.xlsm` into version-controlled YAML/JSON definitions and unit-test them with pytest.
   - Define ingestion schemas (topics, measurement names, engineering units, quality flags, sampling cadence) and store them under `schema/`.
3. **Intelligence Services (Week 2)**
   - Build the FastAPI KPI microservice with local uvicorn workers; connect to TimescaleDB via async SQLAlchemy and expose `/kpi`, `/window`, `/anomaly` endpoints.
   - Add anomaly detection (rule-based thresholds + Z-score/Isolation Forest) running locally with scikit-learn; persist alerts in TimescaleDB.
   - Create the document ingestion pipeline (Python CLI) that extracts text from DOCX/PPTX/PDF, chunks into ~1k tokens, enriches metadata, and upserts into pgvector; include a CLI to rebuild the index from scratch.
   - Encode troubleshooting logic from `Logigramme process/*` into YAML decision trees; create a lightweight rules engine that can be invoked alongside LLM outputs.
   - Stand up Ollama/llama.cpp with the chosen open model; expose a REST endpoint consumed by the orchestrator.
4. **Experience Layer (Week 3)**
   - Implement the agent orchestrator (LangChain/Semantic Kernel) as a Python service with tool abstractions for KPI API, anomaly engine, RAG retriever, rules engine, and chart renderer (Plotly static images served locally).
   - Integrate the local LLM endpoint, ensuring prompts enforce citation formatting and safety callouts; add fallback templates when the LLM response violates guardrails.
   - Build the React/Vite front end with local API gateway (FastAPI or Express) for session management; add WebSocket/SSE streaming, inline citation footers, and chart embeds.
   - Add a scenario runner (CLI + JSON scripts) to replay demo dialogues against the orchestrator and capture outputs for regression tests.
5. **Validation & Demo Prep (Week 4)**
   - Run scripted scenarios (e.g., rendement drop) using the scenario runner; log metrics locally (Prometheus/Grafana) for response latency, relevance score, citation accuracy, recommendation quality, anomaly precision/recall.
   - Add observability: instrument services with OpenTelemetry, scrape via Prometheus, and expose Grafana dashboards; run k6/Locust to stress KPI/agent services locally.
   - Finalize deliverables: architecture diagram, operations manual (including how to start/stop each container), on-call checklist, automated pytest suites, and evaluation report stored in `docs/`.

## 4. Additional Considerations

- **Safety:** Every recommendation must state expected impact, risks, and prerequisites; the rules engine should block unsafe advice.
- **Traceability:** Attach timestamps, sensor tags, or document references to each statement so SMEs can audit responses.
- **Extensibility:** Keep simulator, KPI service, RAG index, and orchestrator decoupled via APIs to reuse across plants.
- **Testing:** Combine unit tests (KPI formulas, rule logic), integration tests (tool chaining), and scenario-based acceptance tests replayed before each demo.
