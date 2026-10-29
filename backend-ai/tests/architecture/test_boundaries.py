"""Lightweight architecture tests verifying hexagonal dependency rules via AST analysis."""

import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent.parent / "app"

FORBIDDEN_DATABASE_MODULES = {
    "sqlalchemy",
    "psycopg",
    "psycopg2",
    "asyncpg",
    "tortoise",
    "peewee",
    "sqlmodel",
    "pymongo",
}


KNOWN_APP_SUBPACKAGES = {
    "api",
    "application",
    "contracts",
    "core",
    "domain",
    "infrastructure",
    "observability",
    "ports",
    "prompts",
}


def _get_module_package(file_path: Path) -> list[str]:
    """
    Determine the package segments of a file relative to the project root.

    E.g.
    app/application/matching_service.py -> ['app', 'application']
    app/domain/matching/skill_match.py  -> ['app', 'domain', 'matching']
    """
    try:
        rel = file_path.resolve().relative_to(APP_DIR.parent)
        parts = list(rel.parts)
        return parts[:-1]
    except Exception:
        return ["app"]


def _get_imports(file_path: Path, source: str | None = None) -> list[str]:
    """Parse a python file into an AST and return all imported module names normalized to FQNs."""
    if source is None:
        source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []

    pkg_parts = _get_module_package(file_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                base = node.module or ""
            else:
                # Relative import: node.level leading dots
                # level=1 ('.') is current package; level=2 ('..') is parent package, etc.
                dots_up = node.level - 1
                base_parts = list(pkg_parts[: len(pkg_parts) - dots_up]) if dots_up < len(pkg_parts) else []
                if node.module:
                    base_parts.append(node.module)
                base = ".".join(base_parts)

            # Normalize any subpackage that belongs to 'app' if relative import resolved past 'app'
            if base and not base.startswith("app.") and base != "app":
                first_seg = base.split(".")[0]
                if first_seg in KNOWN_APP_SUBPACKAGES:
                    base = f"app.{base}"

            if base:
                imports.append(base)

            for alias in node.names:
                if base:
                    full = f"{base}.{alias.name}"
                else:
                    full = alias.name
                    if full in KNOWN_APP_SUBPACKAGES:
                        full = f"app.{full}"
                imports.append(full)

    return list(dict.fromkeys(imports))


def _find_violations(file_path: Path, forbidden_modules: set[str], source: str | None = None) -> list[str]:
    """Find all imports matching forbidden module prefixes."""
    violations = []
    for imported in _get_imports(file_path, source=source):
        for forbidden in forbidden_modules:
            if imported == forbidden or imported.startswith(f"{forbidden}."):
                violations.append(f"{file_path.name} imports forbidden '{imported}'")
    return violations


def test_no_database_libraries_in_entire_backend_ai():
    """Rule: backend-ai must NOT import any relational or ORM database libraries."""
    py_files = list(APP_DIR.rglob("*.py"))
    assert len(py_files) > 0

    violations = []
    for py_file in py_files:
        violations.extend(_find_violations(py_file, FORBIDDEN_DATABASE_MODULES))

    assert not violations, "Database library violations detected:\n" + "\n".join(violations)


def test_domain_layer_dependencies():
    """Rule: Domain must not import FastAPI, Starlette, Infrastructure, Ports, or external providers."""
    domain_dir = APP_DIR / "domain"
    domain_files = list(domain_dir.rglob("*.py"))
    assert len(domain_files) > 0

    forbidden_in_domain = {
        "fastapi",
        "starlette",
        "httpx",
        "fitz",
        "openai",
        "anthropic",
        "google",
        "app.infrastructure",
        "app.ports",
        "app.api",
    }

    violations = []
    for py_file in domain_files:
        violations.extend(_find_violations(py_file, forbidden_in_domain))

    assert not violations, "Domain dependency violations detected:\n" + "\n".join(violations)


def test_application_layer_dependencies():
    """Rule: Application orchestrates Domain and Ports, but must NOT import Infrastructure, FastAPI, or API."""
    app_layer_dir = APP_DIR / "application"
    app_files = list(app_layer_dir.rglob("*.py"))
    assert len(app_files) > 0

    forbidden_in_application = {
        "fastapi",
        "starlette",
        "app.api",
        "app.infrastructure",
    }

    violations = []
    for py_file in app_files:
        violations.extend(_find_violations(py_file, forbidden_in_application))

    assert not violations, "Application dependency violations detected:\n" + "\n".join(violations)


def test_infrastructure_layer_dependencies():
    """Rule: Infrastructure implements Ports, but must NEVER import from Application layer."""
    infra_dir = APP_DIR / "infrastructure"
    infra_files = list(infra_dir.rglob("*.py"))
    assert len(infra_files) > 0

    forbidden_in_infra = {
        "app.application",
    }

    violations = []
    for py_file in infra_files:
        violations.extend(_find_violations(py_file, forbidden_in_infra))

    assert not violations, "Infrastructure dependency violations detected:\n" + "\n".join(violations)


def test_api_routes_do_not_import_concrete_providers_directly():
    """Rule: API route modules must depend on Application services, not concrete LLM providers."""
    api_v1_dir = APP_DIR / "api" / "v1"
    api_files = [f for f in api_v1_dir.glob("*.py") if f.name != "__init__.py"]
    assert len(api_files) > 0

    forbidden_in_api = {
        "openai",
        "anthropic",
        "google",
        "app.infrastructure.llm.providers",
        "app.infrastructure.embeddings.providers",
    }

    violations = []
    for py_file in api_files:
        violations.extend(_find_violations(py_file, forbidden_in_api))

    assert not violations, "API route provider violations detected:\n" + "\n".join(violations)


def test_ast_checker_detects_forbidden_imports_and_relative_bypasses():
    """Verify that _get_imports correctly catches absolute and relative import bypasses."""
    app_file = APP_DIR / "application" / "dummy_service.py"
    forbidden_in_application = {
        "fastapi",
        "starlette",
        "app.api",
        "app.infrastructure",
    }

    forbidden_snippets = [
        # 1. Absolute provider imports
        "import app.infrastructure.embeddings.providers.openai_provider",
        "from app.infrastructure.embeddings.providers.openai_provider import OpenAiEmbeddingProvider",
        "from app.infrastructure.llm.providers.openai_provider import OpenAiLlmProvider",
        # 2. Absolute factory imports
        "from app.infrastructure.embeddings.factory import get_embedding_provider",
        "from app.infrastructure.llm.factory import get_llm_provider",
        "import app.infrastructure.embeddings.factory as emb_factory",
        "import app.infrastructure as infra",
        # 3. Relative provider imports
        "from ..infrastructure.embeddings.providers.openai_provider import OpenAiEmbeddingProvider",
        "from ..infrastructure.llm.providers.openai_provider import OpenAiLlmProvider",
        "from ...infrastructure.embeddings.providers import OpenAiEmbeddingProvider",
        # 4. Relative factory imports
        "from ..infrastructure.embeddings.factory import get_embedding_provider",
        "from ..infrastructure.llm.factory import get_llm_provider",
        "from ...infrastructure.embeddings.factory import get_embedding_provider",
        # 5. Relative package imports
        "from .. import infrastructure",
        "from ... import infrastructure",
    ]

    for snippet in forbidden_snippets:
        violations = _find_violations(app_file, forbidden_in_application, source=snippet)
        assert len(violations) > 0, f"Expected violation for Application snippet: {snippet}"

    allowed_snippets = [
        "from app.ports.embeddings import EmbeddingPort",
        "from app.domain.matching.similarity import cosine_similarity",
        "from ..ports.embeddings import EmbeddingPort",
        "from ..domain.matching.similarity import cosine_similarity",
        "from app.contracts.common import ResponseMeta",
    ]

    for snippet in allowed_snippets:
        violations = _find_violations(app_file, forbidden_in_application, source=snippet)
        assert len(violations) == 0, f"Expected NO violation for Application snippet: {snippet}, got: {violations}"


def test_ast_checker_detects_domain_relative_import_violations():
    """Verify that Domain layer relative imports of Ports, Infrastructure, or API are caught."""
    # Nested domain file: app/domain/matching/dummy_domain.py (depth 3)
    domain_matching_file = APP_DIR / "domain" / "matching" / "dummy_domain.py"
    forbidden_in_domain = {
        "app.infrastructure",
        "app.ports",
        "app.api",
    }

    domain_matching_forbidden_snippets = [
        "from ...ports.embeddings import EmbeddingPort",
        "from ...ports.llm import LlmPort",
        "from ...infrastructure.embeddings.factory import get_embedding_provider",
        "from ...infrastructure.embeddings.providers.openai_provider import OpenAiEmbeddingProvider",
        "from ... import ports",
        "from ... import infrastructure",
        "from ... import api",
    ]

    for snippet in domain_matching_forbidden_snippets:
        violations = _find_violations(domain_matching_file, forbidden_in_domain, source=snippet)
        assert len(violations) > 0, f"Expected violation for Domain matching snippet: {snippet}"

    # Top-level domain file: app/domain/dummy_domain.py (depth 2)
    domain_file = APP_DIR / "domain" / "dummy_domain.py"
    domain_forbidden_snippets = [
        "from ..ports.embeddings import EmbeddingPort",
        "from ..infrastructure.embeddings.factory import get_embedding_provider",
        "from .. import ports",
        "from .. import infrastructure",
        "from .. import api",
    ]

    for snippet in domain_forbidden_snippets:
        violations = _find_violations(domain_file, forbidden_in_domain, source=snippet)
        assert len(violations) > 0, f"Expected violation for Domain snippet: {snippet}"

    domain_allowed_snippets = [
        "from app.domain.cv.normalization import normalize_skill",
        "from ..cv.normalization import normalize_skill",
        "from .normalization import normalize_skill",
    ]

    for snippet in domain_allowed_snippets:
        violations = _find_violations(domain_matching_file, forbidden_in_domain, source=snippet)
        assert len(violations) == 0, f"Expected NO violation for Domain snippet: {snippet}, got: {violations}"


def test_experience_match_does_not_import_contract_validators():
    """Rule: app.domain.matching.experience_match must not import app.contracts.validators."""
    exp_file = APP_DIR / "domain" / "matching" / "experience_match.py"
    violations = _find_violations(exp_file, {"app.contracts.validators"})
    assert not violations, "experience_match.py imports forbidden 'app.contracts.validators':\n" + "\n".join(violations)
