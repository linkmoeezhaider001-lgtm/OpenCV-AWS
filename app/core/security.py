"""API-key authentication dependency."""

import os

from fastapi import Header, HTTPException, status


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected_key = os.getenv("API_KEY")
    if not expected_key or x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

