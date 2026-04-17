"""Authentication helpers for the production agent."""
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate the incoming API key header."""
    if not api_key or api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <key>",
        )
    return api_key


def mask_key(key: str) -> str:
    """Return a safe masked representation for logs."""
    if not key:
        return "<unset>"
    if len(key) <= 4:
        return "****"
    return f"{key[:4]}****"
