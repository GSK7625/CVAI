"""Unit tests for education level matching and degree rank extraction."""

from app.domain.matching.education_match import (
    _get_degree_rank,
    calculate_education_match,
)


def test_education_match_meets_requirement():
    """Candidate with required degree receives full score."""
    res = calculate_education_match(candidate_degrees=["Bachelor of Engineering"], required_education="Bachelor")
    assert res.score == 100.0


def test_education_match_no_requirement():
    """No requirement yields 100 score."""
    res = calculate_education_match(candidate_degrees=[], required_education=None)
    assert res.score == 100.0


def test_education_match_lower_degree():
    """Candidate with lower degree receives partial score."""
    res = calculate_education_match(candidate_degrees=["High School"], required_education="Bachelor")
    assert res.score <= 75.0


def test_mba_requirement_vs_bootcamp_certificate():
    """Bootcamp Certificate must NOT match MBA as rank 2; must yield conservative baseline score 50."""
    res = calculate_education_match(
        candidate_degrees=["Bootcamp Certificate"],
        required_education="MBA",
    )
    assert res.score == 50.0
    assert "chưa được xác định tương đương" in res.comparison_text
    assert "MBA" in res.comparison_text


def test_mba_requirement_vs_mba():
    """MBA candidate exactly meets MBA requirement."""
    res = calculate_education_match(
        candidate_degrees=["MBA in Finance"],
        required_education="MBA",
    )
    assert res.score == 100.0
    assert "đáp ứng hoặc vượt" in res.comparison_text


def test_bachelor_requirement_vs_bsc():
    """BSc candidate meets Bachelor requirement via clear alias."""
    res = calculate_education_match(
        candidate_degrees=["BSc in Computer Science"],
        required_education="Bachelor",
    )
    assert res.score == 100.0


def test_master_requirement_vs_bachelor():
    """Bachelor candidate is exactly 1 level below Master requirement (score 75)."""
    res = calculate_education_match(
        candidate_degrees=["Bachelor of Science"],
        required_education="Master",
    )
    assert res.score == 75.0
    assert "gần tương đương" in res.comparison_text


def test_unknown_requirement_vs_known_candidate_degree():
    """Unrecognized job requirement cannot be ordinally compared (score 50 conservative)."""
    res = calculate_education_match(
        candidate_degrees=["Bachelor of Computer Science"],
        required_education="Specialized Guild Credential XYZ",
    )
    assert res.score == 50.0
    assert "chưa được xác định theo khung văn bằng chuẩn" in res.comparison_text


def test_known_requirement_vs_unknown_candidate_degree():
    """Unrecognized candidate degree does not satisfy recognized Bachelor requirement (score 50)."""
    res = calculate_education_match(
        candidate_degrees=["Fullstack Web Development Bootcamp"],
        required_education="Bachelor",
    )
    assert res.score == 50.0
    assert "chưa được xác định tương đương" in res.comparison_text


def test_unknown_requirement_vs_unknown_candidate_degree():
    """Both unrecognized values must NOT falsely return 100; conservative baseline 50."""
    res = calculate_education_match(
        candidate_degrees=["Non-standard Diploma 123"],
        required_education="Non-standard Credential 456",
    )
    assert res.score == 50.0
    assert "chưa được xác định theo khung chuẩn" in res.comparison_text


def test_missing_requirement_whitespace_and_none():
    """Missing or whitespace-only education requirement awards full score 100."""
    res_none = calculate_education_match(candidate_degrees=["High School"], required_education=None)
    assert res_none.score == 100.0

    res_empty = calculate_education_match(candidate_degrees=["High School"], required_education="")
    assert res_empty.score == 100.0

    res_ws = calculate_education_match(candidate_degrees=["High School"], required_education="   ")
    assert res_ws.score == 100.0


def test_missing_candidate_education():
    """Candidate providing no degrees when required receives baseline score 50."""
    res_empty = calculate_education_match(candidate_degrees=[], required_education="Bachelor")
    assert res_empty.score == 50.0
    assert "chưa cung cấp thông tin" in res_empty.comparison_text

    res_blank = calculate_education_match(candidate_degrees=["", "   "], required_education="Bachelor")
    assert res_blank.score == 50.0
    assert "chưa cung cấp thông tin" in res_blank.comparison_text


def test_candidate_exceeds_requirement():
    """Candidate holding a higher degree (e.g. Master) exceeds Bachelor requirement (score 100)."""
    res = calculate_education_match(
        candidate_degrees=["Master of Science in Data Science"],
        required_education="Bachelor",
    )
    assert res.score == 100.0


def test_candidate_multiple_degrees_highest_rank_evaluated():
    """Candidate with both non-degree certificate and valid degree is scored on highest degree."""
    res = calculate_education_match(
        candidate_degrees=["Bootcamp Certificate", "BSc in Software Engineering"],
        required_education="Bachelor",
    )
    assert res.score == 100.0


def test_degree_rank_extraction_and_alias_coverage():
    """Verify _get_degree_rank returns correct ranks for aliases and None for unknowns."""
    # Doctorate (rank 5)
    assert _get_degree_rank("Doctor of Philosophy") == 5
    assert _get_degree_rank("PhD in Robotics") == 5
    assert _get_degree_rank("Ph.D.") == 5
    assert _get_degree_rank("Tiến sĩ Toán tin") == 5

    # Master (rank 4)
    assert _get_degree_rank("Master of Science") == 4
    assert _get_degree_rank("MSc Artificial Intelligence") == 4
    assert _get_degree_rank("MS in CS") == 4
    assert _get_degree_rank("MBA") == 4
    assert _get_degree_rank("M.B.A.") == 4
    assert _get_degree_rank("Thạc sĩ Quản trị Kinh doanh") == 4

    # Bachelor (rank 3)
    assert _get_degree_rank("Bachelor of Engineering") == 3
    assert _get_degree_rank("Bachelor's Degree") == 3
    assert _get_degree_rank("BSc Computer Science") == 3
    assert _get_degree_rank("B.Sc.") == 3
    assert _get_degree_rank("BS in Math") == 3
    assert _get_degree_rank("B.S.") == 3
    assert _get_degree_rank("BEng Software") == 3
    assert _get_degree_rank("B.Eng.") == 3
    assert _get_degree_rank("BE Mechanical") == 3
    assert _get_degree_rank("B.E.") == 3
    assert _get_degree_rank("Cử nhân CNTT") == 3
    assert _get_degree_rank("Kỹ sư Phần mềm") == 3
    assert _get_degree_rank("Đại học Bách Khoa") == 3

    # Associate (rank 2)
    assert _get_degree_rank("Associate Degree") == 2
    assert _get_degree_rank("Cao đẳng Thực hành") == 2

    # High School (rank 1)
    assert _get_degree_rank("High School Diploma") == 1
    assert _get_degree_rank("THPT") == 1
    assert _get_degree_rank("Trung học phổ thông") == 1
    assert _get_degree_rank("Cấp 3") == 1

    # Unknown / Non-degree strings -> None (MUST NOT return 2)
    assert _get_degree_rank("Bootcamp Certificate") is None
    assert _get_degree_rank("Online Course Certificate") is None
    assert _get_degree_rank("Cybersecurity Specialist") is None
    assert _get_degree_rank("Systems Administrator") is None
    assert _get_degree_rank("Fullstack Web Developer") is None
    assert _get_degree_rank("Random Free Text") is None
    assert _get_degree_rank("") is None
    assert _get_degree_rank("   ") is None
    assert _get_degree_rank(None) is None


def test_multiple_degrees_order_invariance():
    """Verify that candidate degree ordering does not affect education score or highest degree evaluation."""
    order_a = ["Bachelor of Computer Science", "Master of Science in AI"]
    order_b = ["Master of Science in AI", "Bachelor of Computer Science"]

    res_a = calculate_education_match(candidate_degrees=order_a, required_education="Master")
    res_b = calculate_education_match(candidate_degrees=order_b, required_education="Master")

    assert res_a.score == 100.0
    assert res_b.score == 100.0
    assert res_a.score == res_b.score


def test_doctorate_exceeds_master_and_bachelor():
    """Verify Doctorate (rank 5) candidate receives 100.0 score against Master (rank 4) and Bachelor (rank 3)."""
    res_vs_master = calculate_education_match(
        candidate_degrees=["PhD in Computer Science"],
        required_education="Master",
    )
    assert res_vs_master.score == 100.0
    assert "đáp ứng hoặc vượt" in res_vs_master.comparison_text

    res_vs_bachelor = calculate_education_match(
        candidate_degrees=["Doctor of Philosophy in Robotics"],
        required_education="Bachelor",
    )
    assert res_vs_bachelor.score == 100.0
    assert "đáp ứng hoặc vượt" in res_vs_bachelor.comparison_text


def test_associate_one_level_below_bachelor():
    """Verify Associate (rank 2) candidate is exactly 1 tier below Bachelor (rank 3), receiving score 75.0."""
    res = calculate_education_match(
        candidate_degrees=["Cao đẳng Thực hành CNTT"],
        required_education="Bachelor",
    )
    assert res.score == 75.0
    assert "gần tương đương" in res.comparison_text


def test_high_school_two_levels_below_bachelor():
    """Verify High School (rank 1) candidate is 2 tiers below Bachelor (rank 3), receiving score 50.0."""
    res = calculate_education_match(
        candidate_degrees=["Tốt nghiệp THPT"],
        required_education="Bachelor",
    )
    assert res.score == 50.0
    assert "thấp hơn mức yêu cầu" in res.comparison_text


def test_high_school_three_levels_below_master():
    """Verify High School (rank 1) candidate is 3 tiers below Master (rank 4), receiving score 50.0."""
    res = calculate_education_match(
        candidate_degrees=["High School Diploma"],
        required_education="Master",
    )
    assert res.score == 50.0
    assert "thấp hơn mức yêu cầu" in res.comparison_text


def test_word_boundary_false_positive_prevention():
    """Verify sub-word occurrences of degree keywords are not falsely matched as degrees via regex word boundaries."""
    # Substring matches: "Masterclass" contains "master" as a sub-word, but is NOT matched due to \b
    assert _get_degree_rank("Masterclass Advanced Prompting") is None
    assert _get_degree_rank("Masterclass Workshop") is None

    res_masterclass = calculate_education_match(
        candidate_degrees=["Masterclass Advanced Prompting"],
        required_education="Bachelor",
    )
    assert res_masterclass.score == 50.0
    assert "chưa được xác định tương đương" in res_masterclass.comparison_text


def test_contextual_false_positive_documented_limitations():
    """
    Document current MVP behavior and known limitations regarding standalone word tokens in non-academic phrases.

    Word boundaries (\b) prevent sub-word matches (e.g., 'Masterclass' -> None),
    but standalone keywords inside non-academic phrases match their corresponding degree tier
    under current deterministic regex rules. This is an intentional MVP tradeoff to preserve
    standard resume degree shorthands ('Master', 'Bachelor', 'Associate', 'MS', 'BS', 'BE').
    """
    # Standalone keywords inside non-degree phrases match the degree tier (documented MVP limitation)
    assert _get_degree_rank("Bachelor Party Organizer") == 3
    assert _get_degree_rank("Bachelor Party Organizing") == 3
    assert _get_degree_rank("Guild Master") == 4
    assert _get_degree_rank("Master Chef") == 4
    assert _get_degree_rank("Master Electrician") == 4
    assert _get_degree_rank("MS Office Certification") == 4
    assert _get_degree_rank("BS Safety Training") == 3
    assert _get_degree_rank("BE Developer") == 3
    assert _get_degree_rank("Associate Software Engineer") == 2

    # In contrast, 'Doctor Who Fan Club' is None because Rank 5 patterns
    # require 'doctorate' / 'doctoral' / 'phd', not standalone 'doctor'
    assert _get_degree_rank("Doctor Who Fan Club") is None


def test_education_score_bounds_and_numeric_types():
    """Verify education matching returns valid float scores strictly bounded in [0.0, 100.0]."""
    test_cases = [
        ([], None),
        ([], "Bachelor"),
        (["High School"], "Doctorate"),
        (["Bachelor"], "Bachelor"),
        (["PhD"], "High School"),
        (["Unknown Degree"], "Bachelor"),
        (["Bachelor"], "Unknown Requirement"),
    ]
    for cand_degs, req_edu in test_cases:
        res = calculate_education_match(candidate_degrees=cand_degs, required_education=req_edu)
        assert isinstance(res.score, float)
        assert 0.0 <= res.score <= 100.0
        assert isinstance(res.comparison_text, str)
        assert len(res.comparison_text) > 0


def test_education_match_none_or_unknown_degree_does_not_award_bachelor_match():
    """Verify that None/empty or Unknown degrees do NOT award positive match points when Bachelor is required."""
    res_empty = calculate_education_match(candidate_degrees=[], required_education="Bachelor")
    assert res_empty.score == 50.0

    res_unknown = calculate_education_match(candidate_degrees=["Unknown"], required_education="Bachelor")
    assert res_unknown.score == 50.0
