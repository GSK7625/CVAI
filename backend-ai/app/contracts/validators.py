"""Reusable validation helpers for Pydantic contracts and matching input boundaries."""

from datetime import date
import math
import re
from typing import Any

from app.core.temporal import ONGOING_DATE_TOKENS

# Central constant bounds
MAX_EXPERIENCE_YEARS: float = 60.0
MAX_SKILL_LENGTH: int = 200
MAX_TITLE_LENGTH: int = 300
MAX_DESCRIPTION_LENGTH: int = 20000


def validate_non_empty_string(v: str, field_name: str, max_length: int = 300) -> str:
    """
    Validate and strip a required non-empty string.

    Rejects:
    - non-string types
    - empty strings
    - whitespace-only strings
    - strings exceeding max_length
    """
    if not isinstance(v, str):
        raise ValueError(f"{field_name} must be a string")
    stripped = v.strip()
    if not stripped:
        raise ValueError(f"{field_name} cannot be empty or whitespace-only")
    if len(stripped) > max_length:
        raise ValueError(f"{field_name} exceeds maximum allowed length of {max_length} characters")
    return stripped


def validate_optional_string(v: str | None, max_length: int = 1000) -> str | None:
    """Strip an optional string, normalizing empty or whitespace-only values to None."""
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError("Value must be a string")
    stripped = v.strip()
    if not stripped:
        return None
    if len(stripped) > max_length:
        raise ValueError(f"Value exceeds maximum allowed length of {max_length} characters")
    return stripped


def validate_skill_list(skills: list[str]) -> list[str]:
    """
    Validate, sanitize, and deduplicate a list of skill/technology strings.

    Rules:
    - Strips leading and trailing whitespace from each element.
    - Rejects empty or whitespace-only elements with a ValueError.
    - Rejects any element exceeding MAX_SKILL_LENGTH (200 chars).
    - Preserves special technical skill notations (e.g., 'C#', '.NET', 'Node.js', 'CI/CD').
    - Deduplicates case-insensitively while preserving first-seen spelling and order.
    """
    if not skills:
        return []

    cleaned_skills: list[str] = []
    seen_lower: set[str] = set()

    for idx, raw_skill in enumerate(skills):
        if not isinstance(raw_skill, str):
            raise ValueError(f"Skill at index {idx} must be a string")
        stripped = raw_skill.strip()
        if not stripped:
            raise ValueError(f"Skill at index {idx} cannot be empty or whitespace-only")
        if len(stripped) > MAX_SKILL_LENGTH:
            raise ValueError(f"Skill '{stripped[:20]}...' at index {idx} exceeds limit of {MAX_SKILL_LENGTH} chars")

        lower_key = stripped.lower()
        if lower_key not in seen_lower:
            seen_lower.add(lower_key)
            cleaned_skills.append(stripped)

    return cleaned_skills


def validate_experience_years(v: Any) -> float:
    """
    Validate that experience years is a finite, non-negative float within [0.0, 60.0].

    Rejects:
    - booleans (e.g. True/False coerced to 1.0/0.0)
    - negative numbers
    - NaN, +Infinity, -Infinity
    - values exceeding MAX_EXPERIENCE_YEARS (60.0)
    """
    if isinstance(v, bool):
        raise ValueError("Boolean values are not valid experience numbers")
    try:
        f_val = float(v)
    except (ValueError, TypeError) as err:
        raise ValueError("Experience must be a valid numeric value") from err

    if math.isnan(f_val) or math.isinf(f_val):
        raise ValueError("Experience must be a finite number (NaN and Infinity are not allowed)")
    if f_val < 0.0:
        raise ValueError("Experience cannot be negative")
    if f_val > MAX_EXPERIENCE_YEARS:
        raise ValueError(f"Experience exceeds maximum allowed limit of {MAX_EXPERIENCE_YEARS} years")
    return f_val


def validate_optional_experience_years(v: Any) -> float | None:
    """Validate optional minimum experience years for job postings."""
    if v is None:
        return None
    return validate_experience_years(v)


def _parse_simple_date(d_val: str | None) -> tuple[int, int, int] | None:
    """Parse date string in YYYY, YYYY-MM, or YYYY-MM-DD format into (year, month, day)."""
    if not d_val:
        return None
    cleaned = d_val.strip()
    if not cleaned or cleaned.lower() in ONGOING_DATE_TOKENS:
        return None

    # YYYY-MM-DD
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", cleaned)
    if m:
        try:
            # Validate real calendar date
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return (d.year, d.month, d.day)
        except ValueError:
            return None

    # YYYY-MM
    m = re.match(r"^(\d{4})-(\d{1,2})$", cleaned)
    if m:
        try:
            d = date(int(m.group(1)), int(m.group(2)), 1)
            return (d.year, d.month, 1)
        except ValueError:
            return None

    # YYYY
    m = re.match(r"^(\d{4})$", cleaned)
    if m:
        try:
            d = date(int(m.group(1)), 1, 1)
            return (d.year, 1, 1)
        except ValueError:
            return None

    return None


def validate_date_order(start_date: str | None, end_date: str | None) -> None:
    """
    Validate chronological order when both start_date and end_date parse to concrete calendar dates.

    Preserves ongoing tokens ('Present', 'Current', 'Ongoing', 'Hiện tại', 'Now') and None without error.
    """
    ps = _parse_simple_date(start_date)
    pe = _parse_simple_date(end_date)
    if ps is not None and pe is not None and ps > pe:
        raise ValueError(f"start_date ({start_date}) cannot be later than end_date ({end_date})")
