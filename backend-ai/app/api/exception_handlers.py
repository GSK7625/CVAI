"""Centralized FastAPI exception handlers with error sanitization."""

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import FutureCvAiException
from app.observability.logging import correlation_id_ctx, get_logger

logger = get_logger(__name__)


def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Construct a consistent, sanitized error JSON response."""
    correlation_id = correlation_id_ctx.get()
    content = {
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "correlation_id": correlation_id,
    }
    return JSONResponse(status_code=status_code, content=content)


async def futurecv_exception_handler(request: Request, exc: FutureCvAiException) -> JSONResponse:
    """Handle custom FutureCvAiException domain/application errors."""
    logger.warning(
        "Application exception: %s | code=%s | status=%d | path=%s",
        exc.message,
        exc.error_code,
        exc.status_code,
        request.url.path,
    )
    return create_error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard FastAPI/Starlette HTTPExceptions."""
    error_code = "HTTP_ERROR"
    if exc.status_code == 401:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        error_code = "FORBIDDEN"
    elif exc.status_code == 404:
        error_code = "NOT_FOUND"

    logger.warning("HTTP %d error on %s: %s", exc.status_code, request.url.path, exc.detail)
    return create_error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=str(exc.detail),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request payload validation errors cleanly."""
    sanitized_errors = []
    for err in exc.errors():
        loc = " -> ".join(str(item) for item in err.get("loc", []))
        sanitized_errors.append(
            {
                "field": loc,
                "message": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            }
        )

    logger.warning("Validation error on %s: %s", request.url.path, sanitized_errors)
    return create_error_response(
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": sanitized_errors},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected server errors, ensuring no stack traces or secrets are leaked."""
    logger.exception("Unhandled server exception on %s: %s", request.url.path, str(exc))
    return create_error_response(
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred. Please contact support.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""
    app.add_exception_handler(FutureCvAiException, futurecv_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
