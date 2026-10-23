"""Ticket chunking, embedding, and persistence service."""

from functools import lru_cache

from sqlalchemy.orm import Session

from app.db_models import Ticket, TicketChunk
from app.schemas import TicketIngestRequest


@lru_cache(maxsize=1)
def _get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def process_and_store_bulk_tickets(
    db: Session, tickets: list[TicketIngestRequest]
) -> tuple[int, int]:
    """Chunk and embed all tickets, then persist them with one commit."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    ticket_rows: list[Ticket] = []
    chunk_specs: list[tuple[Ticket, int, str]] = []

    for ticket in tickets:
        ticket_row = Ticket(
            ticket_id=ticket.ticket_id,
            title=ticket.title,
            description=ticket.description,
            metadata_json=ticket.metadata,
        )
        ticket_rows.append(ticket_row)
        content = f"{ticket.title}\n\n{ticket.description}"
        chunk_specs.extend(
            (ticket_row, index, chunk)
            for index, chunk in enumerate(splitter.split_text(content))
        )

    model = _get_embedding_model()
    embeddings = model.encode([chunk for _, _, chunk in chunk_specs])
    db.add_all(ticket_rows)
    db.add_all(
        [
            TicketChunk(
                ticket=ticket_row,
                chunk_index=chunk_index,
                content=content,
                embedding=embedding.tolist(),
            )
            for (ticket_row, chunk_index, content), embedding in zip(
                chunk_specs, embeddings, strict=True
            )
        ]
    )
    db.commit()
    return len(ticket_rows), len(chunk_specs)

