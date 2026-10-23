"""API schemas for ticket ingestion and health checks."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class TicketIngestRequest(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BulkTicketIngestRequest(BaseModel):
    tickets: list[TicketIngestRequest] = Field(min_length=1)


class BulkTicketIngestResponse(BaseModel):
    total_tickets_processed: int
    total_chunks_created: int
    status: str


class HealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"]
    database: Literal["connected", "error"]
    pgvector_extension: Literal["active", "missing"]
    gemini_api_configured: bool
    timestamp: str


class TicketIngestResponse(BaseModel):
    ticket_id: str
    chunks_created: int
    status: str


class AgentReplyRequest(BaseModel):
    query: str = Field(min_length=1)


class AgentReplyResponse(BaseModel):
    category: str
    reply: str
    sources_used: list[str]
