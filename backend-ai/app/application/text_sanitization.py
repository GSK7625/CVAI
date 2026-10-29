"""
Deterministic text sanitization helper for privacy and PII protection.

Redacts obvious email addresses and phone numbers from free-text fields before
text is passed to external AI services or embeddings.
"""

import re

EMAIL_REDACTED_TOKEN = "[EMAIL_REDACTED]"  # noqa: S105
PHONE_REDACTED_TOKEN = "[PHONE_REDACTED]"  # noqa: S105
# Common aliases
REDACTED_EMAIL_TOKEN = EMAIL_REDACTED_TOKEN
REDACTED_PHONE_TOKEN = PHONE_REDACTED_TOKEN

# Email matching pattern with word boundaries
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Phone number candidate pattern recognizing:
# 1. International numbers (+84..., (+84)..., +1...)
# 2. Domestic Vietnamese numbers starting with 0 (09x, 08x, 07x, 05x, 03x, 02x)
# 3. Numbers with parenthesized area code (024)...
PHONE_CANDIDATE_REGEX = re.compile(
    r"(?:"
    r"(?:\+\d{1,4}[-.\s]?(?:\(?\d{1,4}\)?[-.\s]?)?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,4}(?:[-.\s]?\d{2,4})?)"
    r"|"
    r"(?:\(\+\d{1,4}\)[-.\s]?(?:\(?\d{1,4}\)?[-.\s]?)?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,4}(?:[-.\s]?\d{2,4})?)"
    r"|"
    r"(?:\b0\d{1,3}[-.\s]?(?:\d{2,4}[-.\s]?){2,4}\b)"
    r"|"
    r"(?:\(\d{2,4}\)[-.\s]?(?:\d{2,4}[-.\s]?){2,3}\b)"
    r")"
)


def _redact_phone_match(match: re.Match[str]) -> str:
    """Redact match if it contains between 8 and 15 digits (phone number range)."""
    raw = match.group(0)
    digits = re.sub(r"\D", "", raw)
    if 8 <= len(digits) <= 15:
        # Guard against year ranges (e.g. 2020-2024 or 1998-2002)
        if (
            len(digits) == 8
            and (digits.startswith("19") or digits.startswith("20"))
            and (digits[4:].startswith("19") or digits[4:].startswith("20"))
        ):
            return raw
        return PHONE_REDACTED_TOKEN
    return raw


def sanitize_free_text(text: str | None) -> str:
    """
    Deterministically redact obvious email addresses and phone numbers from free text.

    Preserves surrounding text structure while replacing privacy-sensitive tokens.
    Guarantees:
    - Deterministic and idempotent
    - Safe on empty string or None
    - Does not corrupt numeric literals (e.g. 2024, 3 years, 85%, 50 employees)
    - Replaces emails with [EMAIL_REDACTED] and phones with [PHONE_REDACTED]
    """
    if not text:
        return ""

    redacted = EMAIL_REGEX.sub(EMAIL_REDACTED_TOKEN, text)
    redacted = PHONE_CANDIDATE_REGEX.sub(_redact_phone_match, redacted)
    return redacted.strip()


# Backward-compatible alias
sanitize_semantic_text = sanitize_free_text
