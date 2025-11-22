from __future__ import annotations

import os

import uvicorn

from .api import app


def main() -> None:
    host = os.getenv("ORCH_HOST", "0.0.0.0")
    port = int(os.getenv("ORCH_PORT", "8010"))
    reload_enabled = os.getenv("ORCH_RELOAD", "false").lower() in {"1", "true", "yes"}
    uvicorn.run(app, host=host, port=port, reload=reload_enabled)


if __name__ == "__main__":
    main()
