"""Deterministic experience comparison and evaluation."""

from dataclasses import dataclass
from datetime import date
import re

from app.contracts.cv import WorkExperienceItem
from app.core.temporal import ONGOING_DATE_TOKENS as ONGOING_TOKENS


def is_ongoing_end_date(value: str | None) -> bool:
    """
    Check if end_date represents an ongoing employment indicator.

    Explicitly recognizes None (contract standard) or explicit ongoing tokens.
    Empty string or malformed non-date strings are NOT considered ongoing.
    """
    if value is None:
        return True
    cleaned = value.strip().lower()
    return cleaned in ONGOING_TOKENS


def _parse_iso_date(d_val: str | None, default_day: int = 1) -> date | None:
    """
    Parse a date string in YYYY, YYYY-MM, or YYYY-MM-DD format.
    Returns None if date is missing, blank, ongoing indicator, or invalid.
    """
    if not d_val:
        return None
    cleaned = d_val.strip()
    if not cleaned or cleaned.lower() in ONGOING_TOKENS:
        return None

    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", cleaned)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None

    m = re.match(r"^(\d{4})-(\d{1,2})$", cleaned)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), default_day)
        except ValueError:
            return None

    m = re.match(r"^(\d{4})$", cleaned)
    if m:
        try:
            return date(int(m.group(1)), 1 if default_day == 1 else 12, default_day)
        except ValueError:
            return None

    return None


def _interval_duration_years(start: date, end: date) -> float:
    """Calculate elapsed duration in years between two dates."""
    if start >= end:
        return 0.0
    if start.day == 1 and end.day == 1:
        months = (end.year - start.year) * 12 + (end.month - start.month)
        return round(months / 12.0, 1)
    return round((end - start).days / 365.25, 1)


def _merge_date_intervals(intervals: list[tuple[date, date]]) -> list[tuple[date, date]]:
    """Merge overlapping and adjacent calendar date intervals."""
    valid = [iv for iv in intervals if iv[0] < iv[1]]
    if not valid:
        return []
    valid.sort(key=lambda x: (x[0], x[1]))
    merged = [valid[0]]
    for cur_s, cur_e in valid[1:]:
        prev_s, prev_e = merged[-1]
        if cur_s <= prev_e:
            merged[-1] = (prev_s, max(prev_e, cur_e))
        else:
            merged.append((cur_s, cur_e))
    return merged


def calculate_total_experience_years(
    work_experiences: list[WorkExperienceItem],
    reference_date: date | None = None,
) -> float:
    """
    Calculate total cumulative years of work experience with timeline interval merging.

    Overlap & Timeline Resolution Policy:
    1. Empty experience returns 0.0.
    2. Exact duplicate entries (matching title, company, dates, and scalar years)
       are deduplicated to prevent accidental re-submission inflation.
    3. Calendar date classification:
       - Truly ongoing role (end_date is None or explicit ongoing token): uses reference_date.
       - Valid historical dates: parse date normally.
       - Malformed end_date (not ongoing and not valid ISO date): rejected from timeline
         calculation; falls back to scalar years_of_experience if available.
       - Malformed start_date: interval cannot be trusted; falls back to scalar years.
       - end_date <= start_date: interval is invalid; falls back to scalar years.
    4. Conservative Mixed Dated + Undated Policy (FIX B):
       - If at least one reliable dated timeline exists: merged dated timeline is the
         authoritative elapsed-time baseline. Scalar-only/undated roles are ignored
         because temporal overlap cannot be mathematically determined without dates,
         preventing fabricated over-counting and score inflation.
       - If NO reliable dated timeline exists: deduplicated scalar years are summed
         as a backward-compatible fallback.
    """
    if not work_experiences:
        return 0.0

    ref_date = reference_date if reference_date is not None else date.today()

    # Deduplicate exact duplicate items
    unique_items: list[WorkExperienceItem] = []
    seen = set()
    for exp in work_experiences:
        key = (
            (exp.job_title or "").strip().lower(),
            exp.company.strip().lower(),
            (exp.start_date or "").strip(),
            (exp.end_date or "").strip(),
            exp.years_of_experience,
            exp.duration.strip().lower(),
        )
        if key not in seen:
            seen.add(key)
            unique_items.append(exp)

    date_intervals: list[tuple[date, date]] = []
    fallback_scalar_years: float = 0.0

    for exp in unique_items:
        s = _parse_iso_date(exp.start_date)
        if s is None:
            # Malformed or missing start_date: cannot trust interval
            if exp.years_of_experience > 0.0:
                fallback_scalar_years += exp.years_of_experience
            continue

        # Check end date
        end: date
        if is_ongoing_end_date(exp.end_date):
            end = ref_date
        else:
            parsed_end = _parse_iso_date(exp.end_date)
            if parsed_end is None:
                # Malformed end_date (not ongoing and not parseable ISO date)
                # DO NOT interpret as ongoing! Reject interval, retain scalar fallback
                if exp.years_of_experience > 0.0:
                    fallback_scalar_years += exp.years_of_experience
                continue
            end = parsed_end

        if s < end:
            date_intervals.append((s, end))
        else:
            # Invalid interval (end <= start)
            if exp.years_of_experience > 0.0:
                fallback_scalar_years += exp.years_of_experience

    if date_intervals:
        merged_intervals = _merge_date_intervals(date_intervals)
        date_years = sum(_interval_duration_years(cur_s, cur_e) for cur_s, cur_e in merged_intervals)
        # Conservative policy: dated timeline is authoritative; undated roles excluded to avoid double-counting
        total = date_years
    else:
        # No dated timeline exists; use deduplicated scalar fallback
        total = fallback_scalar_years

    return round(max(0.0, total), 1)


@dataclass(frozen=True)
class ExperienceMatchResult:
    """Outcome of work experience comparison."""

    score: float
    comparison_text: str
    candidate_years: float
    required_years: float
    is_active: bool = True


def calculate_experience_match(
    candidate_years: float,
    required_years: float | None = None,
) -> ExperienceMatchResult:
    """
    Compare candidate's years of experience against minimum requirement.

    Scoring:
    - If requirement is None or 0: 100.0 (inactive criterion).
    - If candidate meets or exceeds requirement: 100.0 (active).
    - If candidate has partial experience: proportional score (active).
    """
    req_years = required_years or 0.0

    if required_years is None or req_years <= 0.0:
        return ExperienceMatchResult(
            score=100.0,
            comparison_text="Vị trí không yêu cầu số năm kinh nghiệm tối thiểu.",
            candidate_years=candidate_years,
            required_years=0.0,
            is_active=False,
        )

    if candidate_years >= req_years:
        surplus = round(candidate_years - req_years, 1)
        text = (
            f"Ứng viên có {candidate_years:.1f} năm kinh nghiệm, "
            f"đáp ứng hoàn toàn yêu cầu ({req_years:.1f} năm, vượt {surplus:.1f} năm)."
        )
        return ExperienceMatchResult(
            score=100.0,
            comparison_text=text,
            candidate_years=candidate_years,
            required_years=req_years,
            is_active=True,
        )

    # Partial experience
    ratio = max(0.0, candidate_years / req_years)
    score = round(ratio * 100.0, 2)
    bounded_score = max(0.0, min(100.0, score))
    shortage = round(req_years - candidate_years, 1)
    text = (
        f"Ứng viên có {candidate_years:.1f} năm kinh nghiệm, "
        f"thấp hơn yêu cầu {req_years:.1f} năm (thiếu khoảng {shortage:.1f} năm)."
    )

    return ExperienceMatchResult(
        score=bounded_score,
        comparison_text=text,
        candidate_years=candidate_years,
        required_years=req_years,
        is_active=True,
    )
