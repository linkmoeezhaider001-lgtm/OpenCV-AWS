"""Ticket ingestion endpoints."""

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.database import get_db
from app.schemas import BulkTicketIngestRequest, BulkTicketIngestResponse
from app.services.ingestion import process_and_store_bulk_tickets

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/ingest/bulk",
    response_model=BulkTicketIngestResponse,
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("2/minute")
def ingest_bulk_tickets(
    request: Request,
    payload: BulkTicketIngestRequest,
    db: Session = Depends(get_db),
) -> BulkTicketIngestResponse:
    processed, chunks = process_and_store_bulk_tickets(db, payload.tickets)
    return BulkTicketIngestResponse(
        total_tickets_processed=processed,
        total_chunks_created=chunks,
        status="success",
    )

