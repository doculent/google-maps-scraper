"""API key authentication dependency for FastAPI."""

import hmac
import os

from fastapi import Header, HTTPException


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Validate the X-API-Key header against the SCRAPER_API_KEY env var."""
    expected = os.environ.get("SCRAPER_API_KEY", "")
    if not expected or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return x_api_key
