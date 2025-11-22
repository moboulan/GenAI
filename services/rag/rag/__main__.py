from __future__ import annotations

import os

import uvicorn

from .api import app


def main() -> None:
    host = os.getenv("RAG_API_HOST", "0.0.0.0")
    port = int(os.getenv("RAG_API_PORT", "8000"))
    reload_enabled = os.getenv("RAG_API_RELOAD", "false").lower() in {"1", "true", "yes"}
    uvicorn.run(app, host=host, port=port, reload=reload_enabled)


if __name__ == "__main__":
    main()
