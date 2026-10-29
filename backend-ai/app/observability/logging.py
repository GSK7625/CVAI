"""Centralized, PII-safe, structured logging configuration."""

from contextvars import ContextVar
import logging
import sys

# Context variable to hold current request correlation ID across async execution
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")


class CorrelationIdFilter(logging.Filter):
    """Logging filter to inject correlation ID into all log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id attribute to record."""
        record.correlation_id = correlation_id_ctx.get()
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logger with correlation ID injection and safe formatting."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = "%(asctime)s | %(levelname)-8s | [%(correlation_id)s] | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicate logs
    for existing_handler in list(root_logger.handlers):
        root_logger.removeHandler(existing_handler)

    root_logger.addHandler(handler)

    # Suppress verbose third-party logs
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.access").addFilter(CorrelationIdFilter())
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance with correlation ID support."""
    return logging.getLogger(name)
