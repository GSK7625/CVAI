"""Unit tests for deterministic contact PII sanitization (emails and phone numbers)."""

import pytest

from app.application.text_sanitization import (
    EMAIL_REDACTED_TOKEN,
    PHONE_REDACTED_TOKEN,
    sanitize_free_text,
)


@pytest.mark.parametrize(
    "email,expected_fragment",
    [
        ("manh@example.com", EMAIL_REDACTED_TOKEN),
        ("john.doe+jobs@example.co.uk", EMAIL_REDACTED_TOKEN),
        ("candidate_123@company.vn", EMAIL_REDACTED_TOKEN),
        ("recruiter.team@sub.domain.org", EMAIL_REDACTED_TOKEN),
        ("user-name@domain.info", EMAIL_REDACTED_TOKEN),
    ],
)
def test_sanitize_emails(email: str, expected_fragment: str) -> None:
    """Verify common email formats are deterministically redacted."""
    raw = f"Contact me at {email} for opportunities."
    result = sanitize_free_text(raw)
    assert email not in result
    assert expected_fragment in result


@pytest.mark.parametrize(
    "phone",
    [
        "0988123456",
        "0912 345 678",
        "0912-345-678",
        "0988.123.456",
        "+84 988 123 456",
        "+84988123456",
        "(+84) 988 123 456",
        "(+84)988123456",
        "(024) 3825 7888",
        "024.3825.7888",
        "+1 (555) 123-4567",
        "0906666777",
        "0907777888",
        "09 88 12 34 56",
    ],
)
def test_sanitize_phones(phone: str) -> None:
    """Verify Vietnamese and international phone formats are deterministically redacted."""
    raw = f"Call candidate via {phone} during business hours."
    result = sanitize_free_text(raw)
    assert phone not in result
    assert PHONE_REDACTED_TOKEN in result


def test_sanitize_mixed_email_and_phone() -> None:
    """Verify sentences containing both email and phone number are sanitized properly."""
    raw = "My email is manh@example.com and phone is +84 988 123 456."
    result = sanitize_free_text(raw)
    assert "manh@example.com" not in result
    assert "+84 988 123 456" not in result
    assert result == f"My email is {EMAIL_REDACTED_TOKEN} and phone is {PHONE_REDACTED_TOKEN}."


@pytest.mark.parametrize(
    "legitimate_numeric_literal",
    [
        "2024",
        "2025",
        "3 years",
        "2.5 years",
        "85%",
        "100%",
        "1-3 years",
        "50 employees",
        "123 requests/sec",
        "2022-2025",
        "2020 - 2024",
        "1999-2005",
        "2018/2022",
        "Ứng viên có 3 năm kinh nghiệm React từ 2022 đến 2025.",
    ],
)
def test_sanitize_preserves_legitimate_numeric_data(legitimate_numeric_literal: str) -> None:
    """Verify legitimate metrics, dates, and durations are NOT falsely flagged as phone numbers."""
    result = sanitize_free_text(legitimate_numeric_literal)
    assert PHONE_REDACTED_TOKEN not in result
    assert EMAIL_REDACTED_TOKEN not in result
    assert result == legitimate_numeric_literal.strip()


@pytest.mark.parametrize(
    "text",
    [
        "Normal candidate profile with Python, Docker, and Kubernetes.",
        "My email is candidate@example.com and my phone is 0912-345-678.",
        "Worked at ABC Corp from 2020 to 2023 with 100% rating on 12 projects.",
        "",
        "   ",
    ],
)
def test_sanitize_free_text_idempotency(text: str) -> None:
    """Verify sanitize_free_text is strictly idempotent: f(f(x)) == f(x)."""
    first_pass = sanitize_free_text(text)
    second_pass = sanitize_free_text(first_pass)
    assert first_pass == second_pass


def test_sanitize_free_text_none_and_empty() -> None:
    """Verify None, empty strings, and whitespace return empty string without errors."""
    assert sanitize_free_text(None) == ""
    assert sanitize_free_text("") == ""
    assert sanitize_free_text("   \n\t  ") == ""
