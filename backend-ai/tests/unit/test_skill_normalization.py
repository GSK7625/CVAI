import json
from pathlib import Path

from evaluation.matching.evaluate_skill_aliases import run_skill_alias_evaluation

from app.domain.cv.normalization import SKILL_ALIASES, normalize_skill, normalize_skills

# =====================================================================
# 1. Case & Whitespace Normalization
# =====================================================================


def test_case_insensitivity():
    """Verify normalization is case-insensitive for standard and alias forms."""
    assert normalize_skill("React") == "react"
    assert normalize_skill("react") == "react"
    assert normalize_skill("REACT") == "react"
    assert normalize_skill("PyThOn") == "python"
    assert normalize_skill("DoCkEr") == "docker"


def test_whitespace_trimming_and_internal_collapsing():
    """Verify leading/trailing whitespace and consecutive internal spaces are properly normalized."""
    assert normalize_skill("  React  ") == "react"
    assert normalize_skill("\tPython\n") == "python"
    assert normalize_skill("  C   Sharp  ") == "c#"
    assert normalize_skill("React   Native") == "react-native"
    assert normalize_skill("  Amazon   Web   Services  ") == "aws"
    assert normalize_skill("   ") == ""


# =====================================================================
# 2. Punctuation Preservation & Stripping
# =====================================================================


def test_technical_punctuation_preservation():
    """Verify critical technical symbols '#', '.', '+' are preserved during normalization."""
    assert normalize_skill("C#") == "c#"
    assert normalize_skill("c#") == "c#"
    assert normalize_skill(".NET") == ".net"
    assert normalize_skill(".net") == ".net"
    assert normalize_skill("Node.js") == "node.js"
    assert normalize_skill("node.js") == "node.js"
    assert normalize_skill("C++") == "c++"
    assert normalize_skill("c++") == "c++"
    assert normalize_skill("CI/CD") == "ci/cd"


def test_surrounding_punctuation_stripping():
    """Verify extraneous surrounding punctuation is removed without harming inner symbols."""
    assert normalize_skill('"React"') == "react"
    assert normalize_skill("'Docker'") == "docker"
    assert normalize_skill("(Python)") == "python"
    assert normalize_skill("[PostgreSQL]") == "postgresql"
    assert normalize_skill("-FastAPI-") == "fastapi"
    assert normalize_skill(";Redis;") == "redis"


# =====================================================================
# 3. High-Confidence Canonical Aliases
# =====================================================================


def test_high_confidence_skill_aliases():
    """Verify all supported high-confidence canonical aliases map accurately."""
    # React ecosystem
    assert normalize_skill("ReactJS") == "react"
    assert normalize_skill("React.js") == "react"
    assert normalize_skill("react.js") == "react"
    assert normalize_skill("React Native") == "react-native"
    assert normalize_skill("reactnative") == "react-native"
    assert normalize_skill("react-native") == "react-native"

    # Frontend frameworks
    assert normalize_skill("Vue.js") == "vue.js"
    assert normalize_skill("vuejs") == "vue.js"
    assert normalize_skill("Next.js") == "next.js"
    assert normalize_skill("nextjs") == "next.js"

    # Node.js
    assert normalize_skill("Node") == "node.js"
    assert normalize_skill("NodeJS") == "node.js"
    assert normalize_skill("Node.js") == "node.js"

    # Languages
    assert normalize_skill("TS") == "typescript"
    assert normalize_skill("TypeScript") == "typescript"
    assert normalize_skill("JS") == "javascript"
    assert normalize_skill("JavaScript") == "javascript"
    assert normalize_skill("Py") == "python"
    assert normalize_skill("Python") == "python"
    assert normalize_skill("Golang") == "go"
    assert normalize_skill("Go") == "go"
    assert normalize_skill("C#") == "c#"
    assert normalize_skill("CSharp") == "c#"
    assert normalize_skill("C Sharp") == "c#"
    assert normalize_skill("C++") == "c++"
    assert normalize_skill("CPP") == "c++"

    # .NET family
    assert normalize_skill(".NET") == ".net"
    assert normalize_skill("DotNet") == ".net"
    assert normalize_skill(".NET Core") == ".net"
    assert normalize_skill("ASP.NET") == "asp.net"
    assert normalize_skill("ASP.NET Core") == "asp.net"

    # Infrastructure & Databases
    assert normalize_skill("K8s") == "kubernetes"
    assert normalize_skill("Kubernetes") == "kubernetes"
    assert normalize_skill("Postgres") == "postgresql"
    assert normalize_skill("PostgreSQL") == "postgresql"
    assert normalize_skill("Mongo") == "mongodb"
    assert normalize_skill("MongoDB") == "mongodb"

    # Cloud & DevOps
    assert normalize_skill("AWS") == "aws"
    assert normalize_skill("Amazon Web Services") == "aws"
    assert normalize_skill("GCP") == "gcp"
    assert normalize_skill("Google Cloud") == "gcp"
    assert normalize_skill("Google Cloud Platform") == "gcp"
    assert normalize_skill("Azure") == "azure"
    assert normalize_skill("CI/CD") == "ci/cd"
    assert normalize_skill("CICD") == "ci/cd"


# =====================================================================
# 4. Normalization Idempotency
# =====================================================================


def test_normalization_idempotency():
    """Verify that normalize_skill is strictly idempotent across all aliases and raw inputs."""
    test_inputs = [
        "React",
        "ReactJS",
        "React.js",
        "C++",
        "CPP",
        "C#",
        "C Sharp",
        "CSharp",
        ".NET",
        "DotNet",
        "AWS",
        "Amazon Web Services",
        "CI/CD",
        "CICD",
        "Node.js",
        "Vue.js",
        "PostgreSQL",
        "Kubernetes",
        "RandomCustomLibrary",
    ]
    for skill in test_inputs:
        normalized_once = normalize_skill(skill)
        normalized_twice = normalize_skill(normalized_once)
        assert normalized_once == normalized_twice, f"Idempotency failed for: {skill}"

    # Also verify all dictionary values in SKILL_ALIASES normalize to themselves
    for _alias, canonical in SKILL_ALIASES.items():
        assert normalize_skill(canonical) == canonical, f"Canonical target not self-normalizing: {canonical}"


# =====================================================================
# 5. False Positive Protection & Negative Invariants
# =====================================================================


def test_false_positive_prevention_negative_invariants():
    """Verify critical negative invariants prevent false matches between distinct technologies."""
    # Java != JavaScript
    assert normalize_skill("Java") != normalize_skill("JavaScript")
    assert normalize_skill("Java") == "java"
    assert normalize_skill("JavaScript") == "javascript"

    # React != React Native
    assert normalize_skill("React") != normalize_skill("React Native")
    assert normalize_skill("ReactJS") != normalize_skill("React Native")
    assert normalize_skill("React") == "react"
    assert normalize_skill("React Native") == "react-native"

    # C != C# != C++
    assert normalize_skill("C") != normalize_skill("C#")
    assert normalize_skill("C") != normalize_skill("C++")
    assert normalize_skill("C#") != normalize_skill("C++")
    assert normalize_skill("C") == "c"
    assert normalize_skill("C#") == "c#"
    assert normalize_skill("C++") == "c++"
    assert normalize_skill("CPP") == "c++"

    # SQL != NoSQL
    assert normalize_skill("SQL") != normalize_skill("NoSQL")
    assert normalize_skill("SQL") == "sql"
    assert normalize_skill("NoSQL") == "nosql"

    # .NET != ASP.NET
    assert normalize_skill(".NET") != normalize_skill("ASP.NET")
    assert normalize_skill("DotNet") != normalize_skill("ASP.NET Core")
    assert normalize_skill(".NET") == ".net"
    assert normalize_skill("ASP.NET") == "asp.net"

    # Vue.js != Vuex
    assert normalize_skill("Vue.js") != normalize_skill("Vuex")
    assert normalize_skill("VueJS") != normalize_skill("Vuex")
    assert normalize_skill("Vuex") == "vuex"

    # Python != PyTorch
    assert normalize_skill("Python") != normalize_skill("PyTorch")
    assert normalize_skill("PyTorch") == "pytorch"


# =====================================================================
# 6. Set-Level Deduplication
# =====================================================================


def test_normalize_skills_set_deduplication():
    """Verify normalize_skills eliminates alias duplicates while preserving distinct technologies."""
    raw_skills = [
        "React",
        "ReactJS",
        "react.js",
        "C++",
        "cpp",
        "AWS",
        "Amazon Web Services",
        "Docker",
    ]
    normalized_set = normalize_skills(raw_skills)
    assert len(normalized_set) == 4
    assert normalized_set == {"react", "c++", "aws", "docker"}


# =====================================================================
# 7. Dedicated Skill Alias Dataset Verification
# =====================================================================


def test_dedicated_skill_alias_cases_dataset():
    """Verify all 10 canonical alias evaluation cases from skill_alias_cases.json pass with 0 regressions."""
    dataset_path = (
        Path(__file__).parent.parent.parent / "evaluation" / "matching" / "datasets" / "skill_alias_cases.json"
    )
    with dataset_path.open(encoding="utf-8") as f:
        cases = json.load(f)

    metrics = run_skill_alias_evaluation(cases)
    assert metrics["total"] == 10
    assert metrics["passed"] == 10
    assert metrics["failed"] == 0
    assert metrics["false_positives"] == 0
    assert metrics["false_negatives"] == 0
