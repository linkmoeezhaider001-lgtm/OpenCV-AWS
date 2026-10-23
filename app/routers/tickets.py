"""Ticket ingestion and agent-reply endpoints."""

from fastapi import APIRouter, Depends, status

from app.core.security import verify_api_key
from app.schemas import (
    AgentReplyRequest,
    AgentReplyResponse,
    TicketIngestRequest,
    TicketIngestResponse,
)

router = APIRouter(
    prefix="/tickets",
    dependencies=[Depends(verify_api_key)],
)
_tickets: dict[str, TicketIngestRequest] = {}


@router.post(
    "/ingest",
    response_model=TicketIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_ticket(ticket: TicketIngestRequest) -> TicketIngestResponse:
    """Store a ticket for deterministic local retrieval."""
    _tickets[ticket.ticket_id] = ticket
    chunks_created = max(1, len(ticket.description.split()) // 150 + 1)
    return TicketIngestResponse(
        ticket_id=ticket.ticket_id,
        chunks_created=chunks_created,
        status="success",
    )


@router.post("/agent-reply", response_model=AgentReplyResponse)
def agent_reply(payload: AgentReplyRequest) -> AgentReplyResponse:
    """Classify a query and cite matching ingested tickets."""
    query = payload.query.lower()
    billing_terms = ("refund", "invoice", "billing", "charged", "payment")
    if any(term in query for term in billing_terms):
        return AgentReplyResponse(
            category="billing",
            reply="Your billing request has been classified for billing support.",
            sources_used=[],
        )

    query_terms = set(query.split())
    sources = [
        ticket_id
        for ticket_id, ticket in _tickets.items()
        if query_terms.intersection(
            f"{ticket.title} {ticket.description}".lower().split()
        )
    ]
    return AgentReplyResponse(
        category="technical_rag" if sources else "general",
        reply="Relevant technical ticket context was found." if sources else "No matching ticket context was found.",
        sources_used=sources,
    )


def clear_ticket_store() -> None:
    """Clear local ticket state for isolated tests and process resets."""
    _tickets.clear()
