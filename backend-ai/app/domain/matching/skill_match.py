"""Deterministic skill matching logic with canonical normalization."""

from dataclasses import dataclass, field

from app.domain.cv.normalization import normalize_skill


@dataclass(frozen=True)
class SkillMatchResult:
    """Outcome of skill comparison."""

    matched_required_skills: list[str] = field(default_factory=list)
    missing_required_skills: list[str] = field(default_factory=list)
    matched_preferred_skills: list[str] = field(default_factory=list)
    missing_preferred_skills: list[str] = field(default_factory=list)
    skill_score: float = 0.0
    matched_required_count: int = 0
    total_required_count: int = 0
    is_active: bool = True

    @property
    def matched_skills(self) -> list[str]:
        return list(self.matched_required_skills) + [
            f"{s} (Preferred)" for s in self.matched_preferred_skills
        ]

    @property
    def missing_skills(self) -> list[str]:
        return list(self.missing_required_skills)


def _deduplicate_canonical_skills(skills: list[str]) -> dict[str, str]:
    """
    Deduplicate skills by their canonical normalized form while preserving first-seen display casing.

    Returns an ordered mapping of canonical_skill -> first_seen_display_string.
    """
    canonical_map: dict[str, str] = {}
    for skill in skills:
        cleaned = skill.strip()
        if not cleaned:
            continue
        canonical = normalize_skill(cleaned)
        if canonical not in canonical_map:
            canonical_map[canonical] = cleaned
    return canonical_map


def calculate_skill_match(
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str] | None = None,
) -> SkillMatchResult:
    """
    Compare candidate skills against job required and preferred skills.

    Scoring semantics:
    - CASE A (required + preferred): (matched_req / total_req * 80) + (matched_pref / total_pref * 20)
    - CASE B (required only): (matched_req / total_req * 100)
    - CASE C (preferred only): (matched_pref / total_pref * 100)
    - CASE D (no required & no preferred skills): 100.0 (neutral criterion)
    """
    # 1. Canonical deduplication for required and preferred skills
    req_map = _deduplicate_canonical_skills(required_skills)
    raw_pref_map = _deduplicate_canonical_skills(preferred_skills or [])

    # Disjoint: any preferred skill that canonically overlaps with required is removed
    pref_map = {k: v for k, v in raw_pref_map.items() if k not in req_map}

    # 2. Canonical deduplication for candidate skills
    cand_canonical_set = {normalize_skill(s) for s in candidate_skills if s.strip()}

    # 3. Match evaluation
    matched_required_skills: list[str] = []
    missing_required_skills: list[str] = []

    matched_req_count = 0
    for canon, display in req_map.items():
        if canon in cand_canonical_set:
            matched_req_count += 1
            matched_required_skills.append(display)
        else:
            missing_required_skills.append(display)

    total_req = len(req_map)

    matched_preferred_skills: list[str] = []
    missing_preferred_skills: list[str] = []

    matched_pref_count = 0
    for canon, display in pref_map.items():
        if canon in cand_canonical_set:
            matched_pref_count += 1
            matched_preferred_skills.append(display)
        else:
            missing_preferred_skills.append(display)

    total_pref = len(pref_map)

    # 4. Compute score based on explicit four cases
    if total_req > 0 and total_pref > 0:
        # CASE A: required (80%) + preferred (20%)
        total_skill_score = (matched_req_count / total_req * 80.0) + (matched_pref_count / total_pref * 20.0)
        is_active = True
    elif total_req > 0 and total_pref == 0:
        # CASE B: required only (100%)
        total_skill_score = (matched_req_count / total_req) * 100.0
        is_active = True
    elif total_req == 0 and total_pref > 0:
        # CASE C: preferred only (100%)
        total_skill_score = (matched_pref_count / total_pref) * 100.0
        is_active = True
    else:
        # CASE D: no skill requirements specified (inactive criterion)
        total_skill_score = 100.0
        is_active = False

    bounded_score = max(0.0, min(100.0, total_skill_score))

    return SkillMatchResult(
        matched_required_skills=matched_required_skills,
        missing_required_skills=missing_required_skills,
        matched_preferred_skills=matched_preferred_skills,
        missing_preferred_skills=missing_preferred_skills,
        skill_score=round(bounded_score, 2),
        matched_required_count=matched_req_count,
        total_required_count=total_req,
        is_active=is_active,
    )
