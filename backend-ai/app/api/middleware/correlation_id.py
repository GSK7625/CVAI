"""Correlation ID middleware for distributed request tracing."""

from collections.abc import Awaitable, Callable
import re
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.logging import correlation_id_ctx

CORRELATION_ID_HEADER = "X-Correlation-Id"
VALID_CORRELATION_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,128}$")


def sanitize_correlation_id(raw_id: str | None) -> str:
    """Validate and sanitize an incoming correlation ID, or generate a fresh UUID4."""
    if raw_id and VALID_CORRELATION_ID_REGEX.match(raw_id):
        return raw_id
    return str(uuid.uuid4())


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts or generates a correlation ID and sets it in context and response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request and attach correlation ID."""
        raw_id = request.headers.get(CORRELATION_ID_HEADER)
        cid = sanitize_correlation_id(raw_id)

        token = correlation_id_ctx.set(cid)
        try:
            response = await call_next(request)
            response.headers[CORRELATION_ID_HEADER] = cid
            return response
        finally:
            correlation_id_ctx.reset(token)
