"""Unit tests for skill normalization and matching calculation."""

from app.domain.cv.normalization import normalize_skill, normalize_skills
from app.domain.matching.skill_match import calculate_skill_match


def test_normalize_skill_aliases():
    """Verify alias mapping to canonical skill names."""
    assert normalize_skill("ReactJS") == "react"
    assert normalize_skill("React.js") == "react"
    assert normalize_skill("  Node.JS  ") == "node.js"
    assert normalize_skill("K8s") == "kubernetes"
    assert normalize_skill("Dotnet") == ".net"
    assert normalize_skill("C#") == "c#"


def test_normalize_skills_set():
    """Verify deduplication and normalization."""
    skills = ["React", "reactjs", "React.js", "Docker"]
    normalized = normalize_skills(skills)
    assert len(normalized) == 2
    assert "react" in normalized
    assert "docker" in normalized


def test_case_a_required_and_preferred():
    """Case A: Required contributes 80%, Preferred contributes 20%."""
    # 1 of 2 required matched (40 pts) + 1 of 1 preferred matched (20 pts) -> 60 pts
    cand = ["Python", "Kubernetes"]
    req = ["Python", "FastAPI"]
    pref = ["Kubernetes"]

    res = calculate_skill_match(candidate_skills=cand, required_skills=req, preferred_skills=pref)
    assert res.skill_score == 60.0
    assert res.matched_required_count == 1
    assert res.total_required_count == 2
    assert "FastAPI" in res.missing_skills


def test_case_b_required_only_linear_continuity():
    """Case B: Required-only scales linearly up to 100% without discontinuity."""
    req = ["Python", "Docker"]

    # 0 of 2 matched -> 0.0
    res_zero = calculate_skill_match(candidate_skills=[], required_skills=req, preferred_skills=[])
    assert res_zero.skill_score == 0.0

    # 1 of 2 matched -> 50.0 (previously had a bug resulting in 40.0)
    res_partial = calculate_skill_match(candidate_skills=["Python"], required_skills=req, preferred_skills=[])
    assert res_partial.skill_score == 50.0

    # 2 of 2 matched -> 100.0
    res_full = calculate_skill_match(candidate_skills=["Python", "Docker"], required_skills=req, preferred_skills=[])
    assert res_full.skill_score == 100.0


def test_case_c_preferred_only():
    """Case C: Preferred-only scales linearly to 100% when no required skills."""
    pref = ["AWS", "Terraform"]

    res_partial = calculate_skill_match(candidate_skills=["AWS"], required_skills=[], preferred_skills=pref)
    assert res_partial.skill_score == 50.0

    res_full = calculate_skill_match(
        candidate_skills=["AWS", "Terraform"],
        required_skills=[],
        preferred_skills=pref,
    )
    assert res_full.skill_score == 100.0


def test_case_d_no_skill_requirements_neutral():
    """Case D: Job specifying no skills provides neutral score of 100.0."""
    res = calculate_skill_match(candidate_skills=["Python"], required_skills=[], preferred_skills=[])
    assert res.skill_score == 100.0
    assert res.matched_skills == []
    assert res.missing_skills == []


def test_calculate_skill_match_canonical_alias_matching():
    """Verify skills match even when formatted as aliases."""
    cand = ["ReactJS", "K8s", "DotNet"]
    req = ["React", "Kubernetes", ".NET Core"]

    res = calculate_skill_match(candidate_skills=cand, required_skills=req)
    assert res.skill_score == 100.0
    assert len(res.missing_skills) == 0


def test_duplicate_required_skills_deduplication():
    """Verify duplicate required skills do not inflate requirement count or match count."""
    cand = ["Python"]
    req = ["Python", "Python", "Docker"]

    res = calculate_skill_match(candidate_skills=cand, required_skills=req)
    # Deduplicated requirements are Python, Docker (total = 2)
    assert res.total_required_count == 2
    assert res.matched_required_count == 1
    assert res.skill_score == 50.0
    assert res.matched_skills == ["Python"]
    assert res.missing_skills == ["Docker"]


def test_duplicate_preferred_skills_deduplication():
    """Verify duplicate preferred skills do not skew weighting."""
    cand = ["FastAPI", "Docker"]
    req = ["FastAPI"]
    pref = ["Docker", "docker", "DOCKER"]

    res = calculate_skill_match(candidate_skills=cand, required_skills=req, preferred_skills=pref)
    assert res.total_required_count == 1
    assert res.matched_required_count == 1
    # 80% for req + 20% for pref (1/1) = 100.0%
    assert res.skill_score == 100.0
    assert res.matched_skills == ["FastAPI", "Docker (Preferred)"]


def test_required_and_preferred_overlap_disjoint():
    """Verify skills present in both required and preferred are only scored once in required."""
    cand = ["Python"]
    req = ["Python", "PostgreSQL"]
    pref = ["Python", "Docker"]

    res = calculate_skill_match(candidate_skills=cand, required_skills=req, preferred_skills=pref)
    # Python is stripped from preferred because it is required
    # Required: Python (matched), PostgreSQL (missing) -> 1/2 = 40 pts
    # Preferred: Docker (missing) -> 0/1 = 0 pts
    assert res.total_required_count == 2
    assert res.matched_required_count == 1
    assert res.skill_score == 40.0
    assert res.matched_skills == ["Python"]
    assert "Python (Preferred)" not in res.matched_skills
    assert res.missing_skills == ["PostgreSQL"]


def test_alias_duplicate_skills_in_required():
    """Verify alias-equivalent skills in job requirements collapse to single canonical entry."""
    # React + ReactJS
    res_react = calculate_skill_match(
        candidate_skills=["React"],
        required_skills=["React", "ReactJS"],
    )
    assert res_react.total_required_count == 1
    assert res_react.matched_required_count == 1
    assert res_react.skill_score == 100.0
    assert res_react.matched_skills == ["React"]
    assert res_react.missing_skills == []

    # Postgres + PostgreSQL
    res_pg = calculate_skill_match(
        candidate_skills=[],
        required_skills=["PostgreSQL", "postgres"],
    )
    assert res_pg.total_required_count == 1
    assert res_pg.matched_required_count == 0
    assert res_pg.skill_score == 0.0
    assert res_pg.missing_skills == ["PostgreSQL"]

    # K8s + Kubernetes
    res_k8s = calculate_skill_match(
        candidate_skills=["k8s"],
        required_skills=["K8s", "Kubernetes"],
    )
    assert res_k8s.total_required_count == 1
    assert res_k8s.matched_required_count == 1
    assert res_k8s.skill_score == 100.0
    assert res_k8s.matched_skills == ["K8s"]


def test_mixed_casing_and_whitespace_duplicates():
    """Verify whitespace and casing variations are properly canonicalized and deduplicated."""
    res = calculate_skill_match(
        candidate_skills=["docker"],
        required_skills=["  Docker  ", "docker", "DOCKER "],
    )
    assert res.total_required_count == 1
    assert res.matched_required_count == 1
    assert res.skill_score == 100.0
    assert res.matched_skills == ["Docker"]
    assert res.missing_skills == []


def test_candidate_skill_duplicates_and_aliases():
    """Verify candidate skills with duplicates/aliases do not artificially match multiple times."""
    cand = ["Python", "python", "py", "PYTHON"]
    req = ["Python", "FastAPI"]

    res = calculate_skill_match(candidate_skills=cand, required_skills=req)
    assert res.total_required_count == 2
    assert res.matched_required_count == 1
    assert res.skill_score == 50.0
    assert res.matched_skills == ["Python"]
    assert res.missing_skills == ["FastAPI"]


def test_matched_and_missing_skills_uniqueness_and_order():
    """Verify matched_skills and missing_skills maintain uniqueness and deterministic first-seen ordering."""
    req = ["TypeScript", "ts", "React", "reactjs", "Node.js", "nodejs"]
    cand = ["typescript", "node"]

    res = calculate_skill_match(candidate_skills=cand, required_skills=req)
    assert res.total_required_count == 3
    assert res.matched_required_count == 2
    assert res.matched_skills == ["TypeScript", "Node.js"]
    assert res.missing_skills == ["React"]


def test_cpp_and_c_isolation_in_skill_matching():
    """Verify C and C++ do NOT falsely match each other, while CPP correctly matches C++."""
    # Candidate knows only C, Job requires C++ -> Should NOT match (fixes NORM-BUG-001)
    res_c_for_cpp = calculate_skill_match(candidate_skills=["C"], required_skills=["C++"])
    assert res_c_for_cpp.matched_required_count == 0
    assert res_c_for_cpp.skill_score == 0.0
    assert res_c_for_cpp.matched_skills == []
    assert res_c_for_cpp.missing_skills == ["C++"]

    # Candidate knows C++, Job requires C -> Should NOT match
    res_cpp_for_c = calculate_skill_match(candidate_skills=["C++"], required_skills=["C"])
    assert res_cpp_for_c.matched_required_count == 0
    assert res_cpp_for_c.skill_score == 0.0
    assert res_cpp_for_c.matched_skills == []
    assert res_cpp_for_c.missing_skills == ["C"]

    # Candidate knows CPP, Job requires C++ -> Should match as canonical alias
    res_cpp_alias = calculate_skill_match(candidate_skills=["CPP"], required_skills=["C++"])
    assert res_cpp_alias.matched_required_count == 1
    assert res_cpp_alias.skill_score == 100.0
    assert res_cpp_alias.matched_skills == ["C++"]
    assert res_cpp_alias.missing_skills == []


def test_high_confidence_behavioral_aliases():
    """Verify newly added high-confidence aliases match accurately while retaining Job display strings."""
    # C Sharp -> C#
    res_csharp = calculate_skill_match(candidate_skills=["C Sharp"], required_skills=["C#"])
    assert res_csharp.matched_skills == ["C#"]
    assert res_csharp.skill_score == 100.0

    # Amazon Web Services -> AWS
    res_aws = calculate_skill_match(candidate_skills=["Amazon Web Services"], required_skills=["AWS"])
    assert res_aws.matched_skills == ["AWS"]
    assert res_aws.skill_score == 100.0

    # Google Cloud Platform -> GCP
    res_gcp = calculate_skill_match(candidate_skills=["Google Cloud Platform"], required_skills=["GCP"])
    assert res_gcp.matched_skills == ["GCP"]
    assert res_gcp.skill_score == 100.0

    # VueJS -> Vue.js
    res_vue = calculate_skill_match(candidate_skills=["VueJS"], required_skills=["Vue.js"])
    assert res_vue.matched_skills == ["Vue.js"]
    assert res_vue.skill_score == 100.0

    # NextJS -> Next.js
    res_next = calculate_skill_match(candidate_skills=["NextJS"], required_skills=["Next.js"])
    assert res_next.matched_skills == ["Next.js"]
    assert res_next.skill_score == 100.0

    # CICD -> CI/CD
    res_cicd = calculate_skill_match(candidate_skills=["CICD"], required_skills=["CI/CD"])
    assert res_cicd.matched_skills == ["CI/CD"]
    assert res_cicd.skill_score == 100.0


def test_case_a_extreme_and_boundary_scores():
    """Verify Case A mathematical weighting across edge, extreme, and intermediate ratios."""
    req = ["Python", "FastAPI"]
    pref = ["Docker", "Kubernetes"]

    # 1. Full match: 2/2 req (80.0) + 2/2 pref (20.0) -> 100.0
    res_full = calculate_skill_match(
        candidate_skills=["Python", "FastAPI", "Docker", "Kubernetes"],
        required_skills=req,
        preferred_skills=pref,
    )
    assert res_full.skill_score == 100.0
    assert res_full.matched_required_count == 2
    assert res_full.total_required_count == 2
    assert res_full.matched_skills == ["Python", "FastAPI", "Docker (Preferred)", "Kubernetes (Preferred)"]
    assert res_full.missing_skills == []

    # 2. Required all match, preferred zero match: 2/2 req (80.0) + 0/2 pref (0.0) -> 80.0
    res_req_only = calculate_skill_match(
        candidate_skills=["Python", "FastAPI"],
        required_skills=req,
        preferred_skills=pref,
    )
    assert res_req_only.skill_score == 80.0
    assert res_req_only.matched_required_count == 2
    assert res_req_only.total_required_count == 2
    assert res_req_only.matched_skills == ["Python", "FastAPI"]
    assert res_req_only.missing_skills == []

    # 3. Required zero match, preferred all match: 0/2 req (0.0) + 2/2 pref (20.0) -> 20.0
    res_pref_only = calculate_skill_match(
        candidate_skills=["Docker", "Kubernetes"],
        required_skills=req,
        preferred_skills=pref,
    )
    assert res_pref_only.skill_score == 20.0
    assert res_pref_only.matched_required_count == 0
    assert res_pref_only.total_required_count == 2
    assert res_pref_only.matched_skills == ["Docker (Preferred)", "Kubernetes (Preferred)"]
    assert res_pref_only.missing_skills == ["Python", "FastAPI"]

    # 4. Half required + all preferred: 1/2 req (40.0) + 2/2 pref (20.0) -> 60.0
    res_half_req_all_pref = calculate_skill_match(
        candidate_skills=["Python", "Docker", "Kubernetes"],
        required_skills=req,
        preferred_skills=pref,
    )
    assert res_half_req_all_pref.skill_score == 60.0
    assert res_half_req_all_pref.matched_required_count == 1
    assert res_half_req_all_pref.total_required_count == 2
    assert res_half_req_all_pref.matched_skills == ["Python", "Docker (Preferred)", "Kubernetes (Preferred)"]
    assert res_half_req_all_pref.missing_skills == ["FastAPI"]

    # 5. Half required + zero preferred: 1/2 req (40.0) + 0/2 pref (0.0) -> 40.0
    res_half_req_zero_pref = calculate_skill_match(
        candidate_skills=["Python"],
        required_skills=req,
        preferred_skills=pref,
    )
    assert res_half_req_zero_pref.skill_score == 40.0
    assert res_half_req_zero_pref.matched_required_count == 1
    assert res_half_req_zero_pref.missing_skills == ["FastAPI"]

    # 6. Zero match: 0/2 req (0.0) + 0/2 pref (0.0) -> 0.0
    res_zero = calculate_skill_match(
        candidate_skills=[],
        required_skills=req,
        preferred_skills=pref,
    )
    assert res_zero.skill_score == 0.0
    assert res_zero.matched_required_count == 0
    assert res_zero.matched_skills == []
    assert res_zero.missing_skills == ["Python", "FastAPI"]


def test_preferred_match_cannot_mask_required_gap():
    """Verify invariant: Candidate meeting all required outscores candidate meeting only preferred."""
    req = ["Go", "gRPC"]
    pref = ["Redis", "RabbitMQ"]

    res_strong_core = calculate_skill_match(
        candidate_skills=["Go", "gRPC"],
        required_skills=req,
        preferred_skills=pref,
    )
    res_bonus_only = calculate_skill_match(
        candidate_skills=["Redis", "RabbitMQ"],
        required_skills=req,
        preferred_skills=pref,
    )

    # Invariant: 80.0 > 20.0 (by a 60-point margin)
    assert res_strong_core.skill_score == 80.0
    assert res_bonus_only.skill_score == 20.0
    assert res_strong_core.skill_score > res_bonus_only.skill_score
    assert len(res_strong_core.missing_skills) == 0
    assert len(res_bonus_only.missing_skills) == 2


def test_preferred_skills_never_in_missing_skills():
    """Verify missing preferred skills are strictly omitted from missing_skills list."""
    res = calculate_skill_match(
        candidate_skills=["Python"],
        required_skills=["Python"],
        preferred_skills=["Docker", "AWS", "Kubernetes"],
    )
    # Met required Python (80.0), missed all preferred (0/3) -> 80.0
    assert res.skill_score == 80.0
    assert res.matched_skills == ["Python"]
    # missing_skills should NOT contain Docker, AWS, or Kubernetes
    assert res.missing_skills == []


def test_required_dominates_across_aliases():
    """Verify canonical collision resolution removes alias-equivalent skills from preferred."""
    req = ["React", "Postgres"]
    pref = ["ReactJS", "PostgreSQL", "Docker"]

    # Candidate has React and Postgres only
    res = calculate_skill_match(
        candidate_skills=["React", "Postgres"],
        required_skills=req,
        preferred_skills=pref,
    )
    assert res.total_required_count == 2
    assert res.matched_required_count == 2
    # 2/2 req (80.0) + 0/1 pref (0.0) = 80.0
    assert res.skill_score == 80.0
    assert res.matched_skills == ["React", "Postgres"]
    assert "React (Preferred)" not in res.matched_skills
    assert "ReactJS (Preferred)" not in res.matched_skills
    assert res.missing_skills == []

    # Candidate has neither React nor Postgres, but has Docker
    res_docker_only = calculate_skill_match(
        candidate_skills=["Docker"],
        required_skills=req,
        preferred_skills=pref,
    )
    # 0/2 req (0.0) + 1/1 pref (20.0) = 20.0
    assert res_docker_only.skill_score == 20.0
    assert res_docker_only.matched_skills == ["Docker (Preferred)"]
    assert res_docker_only.missing_skills == ["React", "Postgres"]


def test_skill_score_bounded_and_numeric_stability():
    """Verify edge conditions produce stable floats bounded in [0.0, 100.0]."""
    # Empty candidate list across all cases
    assert calculate_skill_match([], [], []).skill_score == 100.0  # Case D
    assert calculate_skill_match([], ["Python"], []).skill_score == 0.0  # Case B
    assert calculate_skill_match([], [], ["Docker"]).skill_score == 0.0  # Case C
    assert calculate_skill_match([], ["Python"], ["Docker"]).skill_score == 0.0  # Case A

    # Whitespace only candidate
    res_ws = calculate_skill_match(["   ", ""], ["Python"], ["Docker"])
    assert res_ws.skill_score == 0.0
    assert res_ws.matched_skills == []
    assert res_ws.missing_skills == ["Python"]

    # 1/3 required, 0 preferred: 1/3 * 100 = 33.33 (rounded to 2 decimals)
    res_third = calculate_skill_match(["A"], ["A", "B", "C"])
    assert res_third.skill_score == 33.33
    assert isinstance(res_third.skill_score, float)
    assert 0.0 <= res_third.skill_score <= 100.0
