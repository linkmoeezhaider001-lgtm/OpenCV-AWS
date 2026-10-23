"""Dependency health-check endpoint."""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(response: Response, db: Session = Depends(get_db)) -> HealthResponse:
    database = "connected"
    pgvector_extension = "active"

    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database = "error"

    if database == "connected":
        try:
            extension = db.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).scalar()
            if extension is None:
                pgvector_extension = "missing"
        except Exception:
            pgvector_extension = "missing"
    else:
        pgvector_extension = "missing"

    gemini_api_configured = bool(os.getenv("GOOGLE_API_KEY"))
    healthy = (
        database == "connected"
        and pgvector_extension == "active"
        and gemini_api_configured
    )
    response.status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="healthy" if healthy else "unhealthy",
        database=database,
        pgvector_extension=pgvector_extension,
        gemini_api_configured=gemini_api_configured,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

