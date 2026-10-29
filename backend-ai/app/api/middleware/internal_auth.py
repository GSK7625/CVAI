"""Internal service authentication between ASP.NET Core and FastAPI."""

import hmac

from fastapi import Header, HTTPException, status

from app.core.config import get_settings
from app.observability.logging import get_logger

logger = get_logger(__name__)

INTERNAL_API_KEY_HEADER = "X-Internal-API-Key"


def verify_internal_api_key(
    x_internal_api_key: str | None = Header(default=None, alias=INTERNAL_API_KEY_HEADER),
) -> None:
    """
    Verify that incoming internal service request contains a valid API key.

    Uses timing-safe comparison (hmac.compare_digest) to prevent timing attacks.
    Exempts development/test environments if INTERNAL_API_KEY is unset.
    """
    settings = get_settings()

    # If internal_api_key is not configured in settings
    if not settings.internal_api_key:
        if settings.is_production:
            logger.error("INTERNAL_API_KEY is not configured in production. Rejecting request.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal authentication service misconfigured",
            )
        # Permissive in local development/test if key is not configured
        return

    # Check incoming key
    if not x_internal_api_key:
        logger.warning("Request rejected: Missing X-Internal-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing internal service API key",
        )

    # Constant-time comparison
    if not hmac.compare_digest(x_internal_api_key.strip(), settings.internal_api_key):
        logger.warning("Request rejected: Invalid X-Internal-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service API key",
        )
