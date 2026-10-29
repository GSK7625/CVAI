"""Contracts representing structured CV data."""

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.contracts.validators import (
    validate_date_order,
    validate_experience_years,
    validate_non_empty_string,
    validate_optional_string,
    validate_skill_list,
)


class WorkExperienceItem(BaseModel):
    """Work experience entry in structured CV."""

    model_config = ConfigDict(extra="forbid")

    job_title: str | None = Field(default=None, max_length=300, description="Job title or role")
    company: str = Field(default="", max_length=200, description="Company or organization name")
    duration: str = Field(default="", max_length=100, description="Period or duration of employment")
    start_date: str | None = Field(
        default=None,
        max_length=50,
        description="Normalized start date (e.g. YYYY-MM or YYYY-MM-DD)",
    )
    end_date: str | None = Field(
        default=None,
        max_length=50,
        description="Normalized end date (e.g. YYYY-MM or YYYY-MM-DD), or None if current/ongoing",
    )
    years_of_experience: float = Field(
        default=0.0,
        ge=0.0,
        le=60.0,
        description="Estimated years of experience in this role (0 to 60)",
    )
    description: str = Field(default="", max_length=8000, description="Key responsibilities and achievements")

    @field_validator("job_title")
    @classmethod
    def validate_job_title(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 300)

    @field_validator("years_of_experience", mode="before")
    @classmethod
    def validate_years_of_experience(cls, v: Any) -> float:
        return validate_experience_years(v)

    @model_validator(mode="after")
    def validate_work_experience_dates(self) -> "WorkExperienceItem":
        validate_date_order(self.start_date, self.end_date)
        return self


class EducationItem(BaseModel):
    """Education entry in structured CV."""

    model_config = ConfigDict(extra="forbid")

    degree: str | None = Field(
        default=None,
        max_length=200,
        description="Degree or qualification (e.g. Bachelor, Master)",
    )
    institution: str = Field(default="", max_length=200, description="University or educational institution")
    field_of_study: str = Field(default="", max_length=200, description="Major or specialization")
    graduation_year: str | None = Field(default=None, max_length=50, description="Year of completion")

    @field_validator("degree")
    @classmethod
    def validate_degree(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 200)

    @field_validator("graduation_year")
    @classmethod
    def validate_graduation_year(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 50)


class ProjectItem(BaseModel):
    """Project entry in structured CV."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=300, description="Project title or name")
    description: str = Field(default="", max_length=8000, description="Project overview and role")
    technologies: list[Annotated[str, Field(max_length=200)]] = Field(
        default_factory=list,
        max_length=100,
        description="Technologies and tools used",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_non_empty_string(v, "name", 300)

    @field_validator("technologies")
    @classmethod
    def validate_technologies(cls, v: list[str]) -> list[str]:
        return validate_skill_list(v)


class StructuredCv(BaseModel):
    """Normalized, structured representation of a candidate's CV."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, max_length=200, description="Candidate full name")
    email: str | None = Field(default=None, max_length=256, description="Candidate email address")
    phone: str | None = Field(default=None, max_length=50, description="Candidate phone number")
    career_summary: str | None = Field(default=None, max_length=4000, description="Professional summary or bio")
    skills: list[Annotated[str, Field(max_length=200)]] = Field(
        default_factory=list,
        max_length=100,
        description="List of technical and soft skills",
    )
    work_experience: list[WorkExperienceItem] = Field(
        default_factory=list,
        max_length=30,
        description="Chronological work history",
    )
    education: list[EducationItem] = Field(
        default_factory=list,
        max_length=20,
        description="Academic background",
    )
    certificates: list[Annotated[str, Field(max_length=300)]] = Field(
        default_factory=list,
        max_length=50,
        description="Certifications and licenses",
    )
    projects: list[ProjectItem] = Field(
        default_factory=list,
        max_length=30,
        description="Key projects completed",
    )
    technologies: list[Annotated[str, Field(max_length=200)]] = Field(
        default_factory=list,
        max_length=100,
        description="Technologies and frameworks",
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 200)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 200)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 50)

    @field_validator("career_summary")
    @classmethod
    def validate_career_summary(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 4000)

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: list[str]) -> list[str]:
        return validate_skill_list(v)

    @field_validator("technologies")
    @classmethod
    def validate_technologies(cls, v: list[str]) -> list[str]:
        return validate_skill_list(v)

    @field_validator("certificates")
    @classmethod
    def validate_certificates(cls, v: list[str]) -> list[str]:
        if not v:
            return []
        cleaned: list[str] = []
        for idx, cert in enumerate(v):
            if not isinstance(cert, str):
                raise ValueError(f"Certificate at index {idx} must be a string")
            stripped = cert.strip()
            if not stripped:
                raise ValueError(f"Certificate at index {idx} cannot be empty or whitespace-only")
            if len(stripped) > 300:
                raise ValueError(f"Certificate '{stripped[:20]}...' exceeds maximum allowed length of 300 characters")
            cleaned.append(stripped)
        return cleaned
