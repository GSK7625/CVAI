"""Contract tests verifying the 11 required Candidate-Job Matching scenarios.

Requirements verified:
1. Full valid CV + Job
2. Fresher with no work experience
3. Missing optional education
4. Empty preferred skills
5. Duplicate skills
6. Unknown degree
7. Multiple experience entries
8. Projects absent
9. Unicode/Vietnamese content
10. Invalid MatchScore payload (rejected)
11. Response with LLM fallback metadata
"""

import json
from pathlib import Path

from pydantic import ValidationError
import pytest

from app.contracts.matching import MatchRequest, MatchResult

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "contracts" / "scenarios"


def load_scenario(filename: str) -> dict:
    """Load scenario JSON fixture."""
    fixture_path = SCENARIOS_DIR / filename
    with fixture_path.open(encoding="utf-8") as f:
        return json.load(f)


def test_scenario_01_full_valid_cv_and_job():
    """Scenario 1: Full valid CV and Job."""
    data = load_scenario("01_full_valid_cv_and_job.json")
    req = MatchRequest.model_validate(data)

    assert req.cv.full_name == "Nguyễn Văn An"
    assert "C#" in req.cv.skills
    assert len(req.cv.work_experience) == 1
    assert req.cv.work_experience[0].job_title == "Backend Developer"
    assert len(req.cv.education) == 1
    assert req.cv.education[0].degree == "Kỹ sư"
    assert len(req.cv.projects) == 1
    assert req.job.title == "Senior .NET Backend Engineer"
    assert req.job.minimum_experience_years == 2.0
    assert "C#" in req.job.required_skills
    assert "Docker" in req.job.preferred_skills

    # Round trip
    dumped = req.model_dump()
    assert MatchRequest.model_validate(dumped) == req


def test_scenario_02_fresher_no_experience():
    """Scenario 2: Fresher with no work experience."""
    data = load_scenario("02_fresher_no_experience.json")
    req = MatchRequest.model_validate(data)

    assert req.cv.work_experience == []
    assert req.cv.full_name == "Trần Thị Bình"
    assert req.job.minimum_experience_years == 0.0


def test_scenario_03_missing_optional_education():
    """Scenario 3: Missing optional education."""
    data = load_scenario("03_missing_optional_education.json")
    req = MatchRequest.model_validate(data)

    assert req.cv.education == []
    assert req.job.education_requirement is None
    assert len(req.cv.work_experience) == 1
    assert req.cv.work_experience[0].years_of_experience == 5.0


def test_scenario_04_empty_preferred_skills():
    """Scenario 4: Empty preferred skills."""
    data = load_scenario("04_empty_preferred_skills.json")
    req = MatchRequest.model_validate(data)

    assert req.job.preferred_skills == []
    assert len(req.job.required_skills) == 3


def test_scenario_05_duplicate_skills():
    """Scenario 5: Duplicate skills deduplicated case-insensitively while preserving first seen."""
    data = load_scenario("05_duplicate_skills.json")
    req = MatchRequest.model_validate(data)

    # In cv: ["SQL", "sql", " SQL ", "Python", "python", "PowerBI"] -> deduplicates to ["SQL", "Python", "PowerBI"]
    assert req.cv.skills == ["SQL", "Python", "PowerBI"]
    # In job required: ["SQL", "sql", "PowerBI"] -> ["SQL", "PowerBI"]
    assert req.job.required_skills == ["SQL", "PowerBI"]
    # In job preferred: ["Python", "python "] -> ["Python"]
    assert req.job.preferred_skills == ["Python"]


def test_scenario_06_unknown_degree():
    """Scenario 6: Unknown degree parses cleanly without rejection."""
    data = load_scenario("06_unknown_degree.json")
    req = MatchRequest.model_validate(data)

    assert req.cv.education[0].degree == "Bootcamp Intensive Certificate"
    assert req.job.education_requirement == "Chứng chỉ nghề hoặc tương đương"


def test_scenario_07_multiple_experience_entries():
    """Scenario 7: Multiple experience entries."""
    data = load_scenario("07_multiple_experience_entries.json")
    req = MatchRequest.model_validate(data)

    assert len(req.cv.work_experience) == 3
    assert req.cv.work_experience[0].company == "MoMo"
    assert req.cv.work_experience[1].company == "ZaloPay"
    assert req.cv.work_experience[2].company == "TMA Solutions"
    assert len(req.cv.education) == 2


def test_scenario_08_projects_absent():
    """Scenario 8: Projects absent."""
    data = load_scenario("08_projects_absent.json")
    req = MatchRequest.model_validate(data)

    assert req.cv.projects == []
    assert req.cv.full_name == "Bùi Văn Long"


def test_scenario_09_unicode_vietnamese_content():
    """Scenario 9: Unicode/Vietnamese content preserves accents and UTF-8 encoding."""
    data = load_scenario("09_unicode_vietnamese_content.json")
    req = MatchRequest.model_validate(data)

    assert req.cv.full_name == "Ngô Hoàng Trọng Nghĩa"
    assert "Xử lý ngôn ngữ tự nhiên" in req.cv.skills
    assert "VinBigdata" in req.cv.work_experience[0].company
    assert req.job.title == "Chuyên viên Cao cấp Trí tuệ Nhân tạo (NLP / LLM)"
    assert req.job.location == "Thành phố Hà Nội"


def test_scenario_10_invalid_match_score_payload():
    """Scenario 10: Invalid MatchScore payload (>100) must be rejected by Pydantic validation."""
    data = load_scenario("10_invalid_match_score_payload.json")
    with pytest.raises(ValidationError) as exc_info:
        MatchResult.model_validate(data)

    assert "match_score" in str(exc_info.value)


def test_scenario_11_response_llm_fallback_meta():
    """Scenario 11: Response with LLM fallback metadata parses cleanly."""
    data = load_scenario("11_response_llm_fallback_meta.json")
    res = MatchResult.model_validate(data)

    assert res.match_score == 82
    assert res.meta.contract_version == "match-result-v1"
    assert res.meta.explanation_mode == "deterministic-fallback"
    assert res.meta.llm_invoked is True
    assert "Điểm phù hợp: 82/100" in res.match_explanation
