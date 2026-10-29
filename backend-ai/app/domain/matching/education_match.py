"""Deterministic education comparison and ranking."""

from dataclasses import dataclass
import re

# Ordinal ranking of academic degrees:
# Rank 5: Doctorate / PhD (Tiến sĩ)
# Rank 4: Master / MBA (Thạc sĩ)
# Rank 3: Bachelor / Engineering / University (Cử nhân, Kỹ sư, Đại học)
# Rank 2: Associate / Vocational (Cao đẳng)
# Rank 1: High School / Secondary (THPT)

DEGREE_PATTERNS: list[tuple[int, list[str]]] = [
    (
        5,
        [
            r"\bdoctorate\b",
            r"\bdoctoral\b",
            r"\bph\.?d\.?\b",
            r"\btiến sĩ\b",
            r"\btien si\b",
            r"\bdoctor of philosophy\b",
        ],
    ),
    (
        4,
        [
            r"\bmaster(?:'s)?\b",
            r"\bmsc\b",
            r"\bm\.sc\.?\b",
            r"\bms\b",
            r"\bm\.s\.?\b",
            r"\bmba\b",
            r"\bm\.b\.a\.?\b",
            r"\bthạc sĩ\b",
            r"\bthac si\b",
            r"\bmaster of science\b",
            r"\bmaster of arts\b",
            r"\bmaster of business administration\b",
        ],
    ),
    (
        3,
        [
            r"\bbachelor(?:'s)?\b",
            r"\bbsc\b",
            r"\bb\.sc\.?\b",
            r"\bbs\b",
            r"\bb\.s\.?\b",
            r"\bbeng\b",
            r"\bb\.eng\.?\b",
            r"\bbe\b",
            r"\bb\.e\.?\b",
            r"\bcử nhân\b",
            r"\bcu nhan\b",
            r"\bkỹ sư\b",
            r"\bky su\b",
            r"\bđại học\b",
            r"\bdai hoc\b",
            r"\bbachelor of engineering\b",
            r"\bbachelor of science\b",
            r"\bbachelor of arts\b",
            r"\bundergraduate\b",
        ],
    ),
    (
        2,
        [
            r"\bassociate(?:'s)?\b",
            r"\bcao đẳng\b",
            r"\bcao dang\b",
        ],
    ),
    (
        1,
        [
            r"\bhigh[ -]?school\b",
            r"\bthpt\b",
            r"\btrung học phổ thông\b",
            r"\btrung hoc pho thong\b",
            r"\bcấp 3\b",
            r"\bcap 3\b",
        ],
    ),
]


@dataclass(frozen=True)
class EducationMatchResult:
    """Outcome of education qualification comparison."""

    score: float
    comparison_text: str
    is_active: bool = True


def _get_degree_rank(degree_str: str | None) -> int | None:
    """
    Extract standard ordinal rank for an academic degree description.

    Returns:
        - 5 for Doctorate / PhD
        - 4 for Master / MBA
        - 3 for Bachelor / Engineering
        - 2 for Associate / College diploma
        - 1 for High School / Secondary
        - None if degree is missing, blank, or unrecognized
    """
    if not degree_str:
        return None
    cleaned = degree_str.strip().lower()
    if not cleaned:
        return None

    for rank, patterns in DEGREE_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                return rank

    return None


def calculate_education_match(
    candidate_degrees: list[str],
    required_education: str | None = None,
) -> EducationMatchResult:
    """
    Compare candidate degree levels with minimum required education level.

    Scoring Policy:
    1. Job has no education requirement: 100%.
    2. Candidate has no education (when required): 50% baseline.
    3. Job requirement unrecognized: 50% conservative baseline.
    4. Candidate degree unrecognized: 50% conservative baseline (do NOT assume Associate).
    5. Both values unrecognized: 50% conservative baseline (never return 100%).
    6. Candidate meets or exceeds requirement: 100%.
    7. Candidate is 1 level below requirement: 75%.
    8. Candidate is 2+ levels below requirement: 50%.
    """
    if not required_education or not required_education.strip():
        return EducationMatchResult(
            score=100.0,
            comparison_text="Vị trí không đặt yêu cầu bắt buộc về bằng cấp học vấn.",
            is_active=False,
        )

    req_str = required_education.strip()
    clean_cand_degrees = [d.strip() for d in candidate_degrees if d and d.strip()]

    if not clean_cand_degrees:
        return EducationMatchResult(
            score=50.0,
            comparison_text=f"Ứng viên chưa cung cấp thông tin bằng cấp. Vị trí yêu cầu: {req_str}.",
        )

    req_rank = _get_degree_rank(req_str)
    cand_ranks = [_get_degree_rank(d) for d in clean_cand_degrees]
    valid_ranks = [r for r in cand_ranks if r is not None]
    highest_cand_rank: int | None = max(valid_ranks) if valid_ranks else None
    cand_str = ", ".join(clean_cand_degrees)

    # Case 6 & 8: Job requirement unrecognized
    if req_rank is None:
        if highest_cand_rank is None:
            # Case 8: Both unrecognized
            return EducationMatchResult(
                score=50.0,
                comparison_text=(
                    f"Yêu cầu học vấn của vị trí ({req_str}) và bằng cấp của ứng viên ({cand_str}) "
                    "chưa được xác định theo khung chuẩn."
                ),
            )
        # Case 6: Job requirement unrecognized, but candidate degree is known
        return EducationMatchResult(
            score=50.0,
            comparison_text=(
                f"Yêu cầu học vấn của vị trí ({req_str}) chưa được xác định theo khung văn bằng chuẩn. "
                f"Bằng cấp của ứng viên: {cand_str}."
            ),
        )

    # Case 7: Candidate degree unrecognized, but Job requirement is recognized
    if highest_cand_rank is None:
        return EducationMatchResult(
            score=50.0,
            comparison_text=(
                f"Bằng cấp của ứng viên ({cand_str}) chưa được xác định tương đương với yêu cầu vị trí ({req_str})."
            ),
        )

    # Both req_rank and highest_cand_rank are recognized
    if highest_cand_rank >= req_rank:
        return EducationMatchResult(
            score=100.0,
            comparison_text=f"Học vấn của ứng viên đáp ứng hoặc vượt yêu cầu vị trí ({req_str}).",
        )
    if highest_cand_rank == req_rank - 1:
        return EducationMatchResult(
            score=75.0,
            comparison_text=f"Bằng cấp của ứng viên gần tương đương yêu cầu ({req_str}).",
        )

    return EducationMatchResult(
        score=50.0,
        comparison_text=f"Bằng cấp của ứng viên thấp hơn mức yêu cầu của vị trí ({req_str}).",
    )
