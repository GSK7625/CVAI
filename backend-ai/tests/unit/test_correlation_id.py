"""Unit tests for Correlation ID middleware and sanitizer."""

import uuid

from app.api.middleware.correlation_id import sanitize_correlation_id


def test_sanitize_correlation_id_valid():
    """Valid correlation IDs should be preserved."""
    cid = "abc-123.XYZ_test"
    assert sanitize_correlation_id(cid) == cid


def test_sanitize_correlation_id_none_or_empty():
    """None or empty correlation IDs should generate a new valid UUID4."""
    cid = sanitize_correlation_id(None)
    assert uuid.UUID(cid)

    cid_empty = sanitize_correlation_id("")
    assert uuid.UUID(cid_empty)


def test_sanitize_correlation_id_malformed_chars():
    """Control characters or script injection attempts should result in a clean new UUID4."""
    malformed = "attack<script>alert(1)</script>"
    cid = sanitize_correlation_id(malformed)
    assert cid != malformed
    assert uuid.UUID(cid)


def test_sanitize_correlation_id_too_long():
    """Excessively long correlation IDs should be discarded and replaced with a clean UUID4."""
    too_long = "a" * 200
    cid = sanitize_correlation_id(too_long)
    assert cid != too_long
    assert uuid.UUID(cid)
