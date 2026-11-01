"""Tests for ticket chunking, embedding, and persistence."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.schemas import TicketIngestRequest
from app.services.ingestion import process_and_store_bulk_tickets


def make_ticket(ticket_id="TCK-1", description="Short ticket description."):
    return TicketIngestRequest(
        ticket_id=ticket_id,
        title="Sample title",
        description=description,
        metadata={"priority": "low"},
    )


@patch("app.services.ingestion._get_embedding_model")
def test_single_short_ticket_produces_one_chunk(mock_get_model):
    mock_model = MagicMock()
    mock_model.encode.return_value = np.zeros((1, 384))
    mock_get_model.return_value = mock_model

    db = MagicMock()
    tickets_processed, chunks_created = process_and_store_bulk_tickets(
        db, [make_ticket()]
    )

    assert tickets_processed == 1
    assert chunks_created == 1
    db.add_all.assert_called()
    db.commit.assert_called_once()


@patch("app.services.ingestion._get_embedding_model")
def test_long_description_is_split_into_multiple_chunks(mock_get_model):
    long_description = " ".join(["word"] * 1000)
    mock_model = MagicMock()
    mock_model.encode.return_value = np.zeros((5, 384))
    mock_get_model.return_value = mock_model

    db = MagicMock()
    tickets_processed, chunks_created = process_and_store_bulk_tickets(
        db, [make_ticket(description=long_description)]
    )

    assert tickets_processed == 1
    assert chunks_created > 1


@patch("app.services.ingestion._get_embedding_model")
def test_multiple_tickets_are_all_persisted(mock_get_model):
    mock_model = MagicMock()
    mock_model.encode.return_value = np.zeros((2, 384))
    mock_get_model.return_value = mock_model

    db = MagicMock()
    tickets = [make_ticket("TCK-1"), make_ticket("TCK-2")]
    tickets_processed, chunks_created = process_and_store_bulk_tickets(db, tickets)

    assert tickets_processed == 2
    assert chunks_created == 2
