"""Contracts representing structured Job data."""

from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator

from app.contracts.validators import (
    validate_non_empty_string,
    validate_optional_experience_years,
    validate_optional_string,
    validate_skill_list,
)


class StructuredJob(BaseModel):
    """Normalized, structured representation of a Job Posting."""

    title: str = Field(max_length=300, description="Job title")
    description: str = Field(default="", max_length=20000, description="Full job description")
    required_skills: list[Annotated[str, Field(max_length=200)]] = Field(
        default_factory=list,
        max_length=100,
        description="Mandatory skills required for the role",
    )
    preferred_skills: list[Annotated[str, Field(max_length=200)]] = Field(
        default_factory=list,
        max_length=100,
        description="Nice-to-have or bonus skills",
    )
    minimum_experience_years: float | None = Field(
        default=None,
        ge=0.0,
        le=60.0,
        description="Minimum years of professional experience required (0 to 60)",
    )
    education_requirement: str | None = Field(
        default=None,
        max_length=1000,
        description="Minimum education degree required (e.g. Bachelor, Master)",
    )
    location: str | None = Field(default=None, max_length=300, description="Job location or remote")
    salary: str | None = Field(default=None, max_length=200, description="Salary or compensation range")
    employment_type: str | None = Field(
        default=None,
        max_length=100,
        description="Full-time, Part-time, Contract, etc.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        return validate_non_empty_string(v, "title", 300)

    @field_validator("required_skills")
    @classmethod
    def validate_required_skills(cls, v: list[str]) -> list[str]:
        return validate_skill_list(v)

    @field_validator("preferred_skills")
    @classmethod
    def validate_preferred_skills(cls, v: list[str]) -> list[str]:
        return validate_skill_list(v)

    @field_validator("minimum_experience_years", mode="before")
    @classmethod
    def validate_minimum_experience_years(cls, v: Any) -> float | None:
        return validate_optional_experience_years(v)

    @field_validator("education_requirement")
    @classmethod
    def validate_education_requirement(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 1000)

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 300)

    @field_validator("salary")
    @classmethod
    def validate_salary(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 200)

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: str | None) -> str | None:
        return validate_optional_string(v, 100)
