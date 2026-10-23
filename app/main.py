"""FastAPI entry point for the agentic vision controller."""

import time

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.controller import decide_action
from app.core.logging import configure_json_logger
from app.models import ControllerAction, PerceptionPayload
from app.routers import health, ingest, tickets

app = FastAPI(title="Agentic Vision Controller", version="1.0.0")
logger = configure_json_logger()
app.state.limiter = ingest.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next) -> Response:
    """Log request metadata and attach process time to the response."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time-MS"] = f"{process_time_ms:.2f}"

    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "HTTP request completed",
        extra={
            "request_method": request.method,
            "url_path": request.url.path,
            "client_ip": client_ip,
            "status_code": response.status_code,
            "process_time_ms": round(process_time_ms, 2),
        },
    )
    return response


@app.post("/decide", response_model=ControllerAction)
def decide(payload: PerceptionPayload) -> ControllerAction:
    """Return the next action for one perception frame."""
    try:
        action = decide_action(payload)
        primary_bounding_box = None
        if payload.defects:
            primary_bounding_box = max(
                payload.defects, key=lambda defect: defect.area
            ).bounding_box
        logger.info(
            "Vision decision completed",
            extra={
                "confidence_score": payload.confidence_score,
                "defect_detected": payload.defect_detected,
                "total_defects": payload.total_defects,
                "selected_action": action.action,
                "primary_bounding_box": primary_bounding_box,
            },
        )
        return action
    except ValueError as exc:
        logger.warning(
            "Vision decision rejected",
            extra={
                "confidence_score": payload.confidence_score,
                "defect_detected": payload.defect_detected,
                "total_defects": payload.total_defects,
                "error": str(exc),
            },
        )
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def root_health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


app.include_router(health.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(tickets.router, prefix="/api/v1")
