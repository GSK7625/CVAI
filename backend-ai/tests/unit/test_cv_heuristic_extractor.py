"""Unit tests for heuristic CV entity extractor and end-to-end PDF / text CV analysis."""

import pytest

from app.application.cv_analyzer import CvAnalyzerService
from app.contracts.cv import StructuredCv
from app.domain.cv.heuristic_extractor import extract_structured_cv_heuristically
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.ports.document_parser import DocumentParserPort


class DummyPdfParser(DocumentParserPort):
    def __init__(self, text: str) -> None:
        self.text = text

    async def parse_pdf(self, file_bytes: bytes) -> str:
        return self.text


SAMPLE_NGUYEN_MINH_KHOA_CV = """\
NGUYEN MINH KHOA
Senior .NET Backend Engineer
Hanoi, Vietnam | +84 912 345 678 | minh.khoa.dev@gmail.com
linkedin.com/in/minhkhoa-dotnet | github.com/minhkhoa-dev

PROFESSIONAL SUMMARY
Backend engineer with 6+ years of experience building scalable web APIs and enterprise backend
systems using .NET and C#. Strong hands-on experience with ASP.NET Core, PostgreSQL, and Docker,
plus practical knowledge of microservices, RESTful API design, caching, authentication, and CI/CD.
Focused on performance, clean architecture, maintainable code, and production reliability.

CORE SKILLS
l Languages & Frameworks: C#, .NET 6/7/8, ASP.NET Core, Entity Framework Core, LINQ
l Databases: PostgreSQL, SQL Server, Redis
l DevOps & Tools: Docker, Docker Compose, Git, GitHub Actions, Azure DevOps, Swagger, Postman
l Architecture: REST APIs, Microservices, Clean Architecture, Dependency Injection, Repository Pattern
l Other: Unit Testing (xUnit), Integration Testing

PROFESSIONAL EXPERIENCE
Senior Backend Engineer | FPT Software
03/2022 - Present | Hanoi, Vietnam
- Architected and built high-performance microservices using .NET 8 and ASP.NET Core.
- Designed relational schemas and optimized queries on PostgreSQL and SQL Server.
- Containerized applications with Docker and automated deployments using CI/CD pipelines.

.NET Software Engineer | CMC Global
06/2019 - 02/2022 | Hanoi, Vietnam
- Developed enterprise web applications with ASP.NET Core and Entity Framework Core.
- Integrated Redis caching and implemented secure JWT authentication.

EDUCATION
Bachelor of Computer Science | Hanoi University of Science and Technology
2015 - 2019

PROJECTS
E-Commerce Microservices Platform
- Built scalable backend services with ASP.NET Core, PostgreSQL, and Docker.
- Implemented event-driven messaging and resilient REST APIs.
"""


def test_heuristic_extractor_parses_sample_cv():
    """Verify heuristic extractor extracts contact, skills, and experience from sample CV."""
    cv: StructuredCv = extract_structured_cv_heuristically(SAMPLE_NGUYEN_MINH_KHOA_CV)

    assert cv.full_name == "NGUYEN MINH KHOA"
    assert cv.email == "minh.khoa.dev@gmail.com"
    assert cv.phone is not None and "912 345 678" in cv.phone
    assert cv.career_summary is not None and "Backend engineer with 6+ years of experience" in cv.career_summary

    # Assert critical tech skills for matching
    skills_lower = [s.lower() for s in cv.skills]
    assert "c#" in skills_lower
    assert ".net" in skills_lower
    assert "asp.net core" in skills_lower
    assert "postgresql" in skills_lower
    assert "docker" in skills_lower
    assert "redis" in skills_lower
    assert "git" in skills_lower

    # Assert work experience
    assert len(cv.work_experience) >= 2
    assert cv.work_experience[0].company == "FPT Software"
    assert cv.work_experience[0].years_of_experience >= 2.0

    # Assert education
    assert len(cv.education) >= 1
    assert "Hanoi University of Science and Technology" in cv.education[0].institution

    # Assert projects
    assert len(cv.projects) >= 1
    assert "E-Commerce Microservices Platform" in cv.projects[0].name


@pytest.mark.asyncio
async def test_cv_analyzer_service_with_mock_llm_end_to_end():
    """Verify CvAnalyzerService produces valid CvAnalysisResponse with raw_text and accurate score."""
    parser = DummyPdfParser(SAMPLE_NGUYEN_MINH_KHOA_CV)
    llm = MockLlmProvider()
    service = CvAnalyzerService(parser=parser, llm=llm)

    response = await service.analyze_pdf(b"dummy_bytes")

    assert response.structured_cv.full_name == "NGUYEN MINH KHOA"
    assert response.cv_score >= 80  # Comprehensive profile scores high
    assert response.raw_text == SAMPLE_NGUYEN_MINH_KHOA_CV
    assert len(response.strengths) > 0
    assert len(response.weaknesses) >= 0

    skills = [s.lower() for s in response.structured_cv.skills]
    assert ".net" in skills
    assert "c#" in skills
    assert "postgresql" in skills
    assert "docker" in skills
