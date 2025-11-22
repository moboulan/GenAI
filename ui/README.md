# Web UI

React + Vite single-page app that hosts the chat interface, renders KPI/RAG answers from the orchestrator, and will later embed charts and scripted scenarios.

## Getting Started

```bash
cd ui
npm install          # (or pnpm/yarn)
cp .env.example .env # adjust VITE_ORCH_BASE_URL if needed
npm run dev
```

By default the UI targets `http://localhost:8010/chat`, which is the orchestrator endpoint exposed by Docker Compose.

## Structure

| Path | Purpose |
| --- | --- |
| `src/components/Chat.tsx` | Stateful chat shell with input composer, cited sources, and recommendation list. |
| `src/api/orchestrator.ts` | Thin client around the `/chat` endpoint with env-configurable base URL. |
| `src/styles.css` | Minimal styling inspired by the design brief (chips, bubbles, footer). |

Future work will add KPI charts, historical conversation playback, and scenario runners under `scripts/`.
