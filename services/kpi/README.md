# KPI Service

FastAPI microservice exposing KPI computations over the historian plus higher level analytics
such as formula evaluation, trend checks, and anomaly flags.

## Running Against TimescaleDB

1. Start infrastructure: `docker compose up -d timescaledb` from the repo root.
2. Seed fresh measurements (optional but recommended):

    ```bash
    cd services/kpi
    /home/moboulan/Desktop/Industrial_Gen_AI/Code/.venv/bin/python -m app.scripts.seed_timescale --truncate
    ```

   Adjust `--hours`, `--interval-minutes`, or `--dsn` to target a different Timescale instance. Data is reproducible via the `--seed` flag.
3. Launch the API pointed at the live database:

    ```bash
    KPI_TIMESCALE_DSN=postgresql+psycopg://tsp:tsp_pass@localhost:5432/tsp /home/moboulan/Desktop/Industrial_Gen_AI/Code/.venv/bin/python -m uvicorn app.api:app --reload
    ```

4. Validate formulas using the shared registry:

    ```bash
    cd services/kpi
    /home/moboulan/Desktop/Industrial_Gen_AI/Code/.venv/bin/python -m app.scripts.validate_formulas --pretty
    ```

   Pass `--formula rendement` or `--window 120` to focus on specific KPIs/windows.

## Available Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Basic readiness check |
| GET | `/kpi` | Raw tag statistics (avg/min/max/latest) over a rolling window |
| GET | `/kpi/formulas` | List declarative KPI formulas sourced from YAML |
| GET | `/kpi/formulas/{name}` | Evaluate a formula, returning the computed value and input windows |
| GET | `/kpi/trend` | Direction, delta, and slope for a tag across a window |
| GET | `/kpi/anomaly` | Z-score based anomaly flag for the latest sample in the window |

## Testing

```bash
cd services/kpi
/home/moboulan/Desktop/Industrial_Gen_AI/Code/.venv/bin/python -m pytest
```
