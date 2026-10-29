"""Domain and application exceptions for FutureCV AI Service."""

from typing import Any


class FutureCvAiError(Exception):
    """Base exception for all FutureCV AI Service domain and application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


# Backward compatibility alias
FutureCvAiException = FutureCvAiError


class InternalAuthError(FutureCvAiError):
    """Raised when internal service authentication fails."""

    def __init__(self, message: str = "Invalid or missing internal service API key") -> None:
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
        )


class DocumentParsingError(FutureCvAiError):
    """Raised when document parsing or extraction fails."""

    def __init__(
        self,
        message: str = "Failed to parse document content",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="INVALID_DOCUMENT",
            status_code=422,
            details=details,
        )


class DocumentSizeLimitExceededError(FutureCvAiError):
    """Raised when uploaded document exceeds size limit."""

    def __init__(self, max_size_bytes: int, actual_size_bytes: int) -> None:
        super().__init__(
            message=f"Document exceeds maximum allowed size of {max_size_bytes} bytes",
            error_code="FILE_TOO_LARGE",
            status_code=413,
            details={"max_size_bytes": max_size_bytes, "actual_size_bytes": actual_size_bytes},
        )


class DocumentPageLimitExceededError(FutureCvAiError):
    """Raised when uploaded PDF exceeds maximum allowed pages."""

    def __init__(self, max_pages: int, actual_pages: int) -> None:
        super().__init__(
            message=f"Document exceeds maximum allowed page count of {max_pages}",
            error_code="PAGE_LIMIT_EXCEEDED",
            status_code=422,
            details={"max_pages": max_pages, "actual_pages": actual_pages},
        )


class ProviderError(FutureCvAiError):
    """Raised when external AI provider fails or returns invalid response."""

    def __init__(
        self,
        message: str = "AI Provider error occurred during computation",
        provider: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        err_details = details or {}
        if provider:
            err_details["provider"] = provider
        super().__init__(
            message=message,
            error_code="AI_PROVIDER_ERROR",
            status_code=502,
            details=err_details,
        )


class RateLimitExceededError(FutureCvAiError):
    """Raised when an external AI provider rate limit is encountered."""

    def __init__(self, message: str = "Rate limit exceeded from AI provider") -> None:
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )


class ValidationError(FutureCvAiError):
    """Raised when input validation fails in domain or application logic."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )
