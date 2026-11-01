# Agentic Vision Controller

This service evaluates OpenCV perception metadata and selects the next action in
the perception-decision-action loop:

- High-confidence defects (`confidence_score >= 0.85`) produce
  `flag_defect_alert`.
- Ambiguous detections produce `update_vision_config`, enabling CLAHE, lowering
  Canny thresholds, and creating a 20%-padded, frame-clamped ROI.
- Clear frames produce `pass_frame`; an active ROI is reset to `null`.

It also includes a ticket-ingestion/RAG subsystem for routing and answering
support queries using embedded ticket content.

## Endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/decide` | none | Evaluate a `PerceptionPayload` and return a `ControllerAction` |
| GET | `/health` | none | Basic liveness check |
| GET | `/api/v1/health` | none | Dependency health check (DB, pgvector, Gemini key) |
| POST | `/api/v1/ingest/bulk` | `X-API-Key` | Chunk, embed, and persist a batch of tickets (rate-limited, 2/min) |
| POST | `/api/v1/tickets/ingest` | `X-API-Key` | Store a single ticket locally |
| POST | `/api/v1/tickets/agent-reply` | `X-API-Key` | Classify a query and cite matching ingested tickets |

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./agentic_vision.db` | SQLAlchemy connection string (Postgres+pgvector in Docker) |
| `API_KEY` | none | Required value for the `X-API-Key` header on protected routes |
| `GOOGLE_API_KEY` | none | Marks the Gemini integration as configured in `/api/v1/health` |

## Run locally

From the project root:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Send a payload to `http://127.0.0.1:8000/decide` using the shape in
[`sample_payload.json`](sample_payload.json).

## Run with Docker Compose

```bash
docker compose up --build
```

This starts the API on port `8000` and a `pgvector/pgvector:pg16` Postgres
instance on port `5432`. Set `API_KEY` and `GOOGLE_API_KEY` in your shell or a
`.env` file before starting to override the Compose defaults.

## Test

```powershell
.\venv\Scripts\python.exe -m pytest
```

Continuous integration runs the same suite on every push and pull request via
[`.github/workflows/tests.yml`](.github/workflows/tests.yml).
