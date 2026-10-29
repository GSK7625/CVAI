using System.Text.Json.Serialization;

namespace FutureCV.Application.Features.AiMatching.DTOs;

// =============================================================================
// AI Matching Engine Request Contracts (v1)
// Aligned with Python FastAPI MatchRequest / StructuredCv / StructuredJob
// =============================================================================

public sealed record AiWorkExperienceDto(
    [property: JsonPropertyName("job_title")] string? JobTitle = null,
    [property: JsonPropertyName("company")] string Company = "",
    [property: JsonPropertyName("duration")] string Duration = "",
    [property: JsonPropertyName("start_date")] string? StartDate = null,
    [property: JsonPropertyName("end_date")] string? EndDate = null,
    [property: JsonPropertyName("years_of_experience")] double YearsOfExperience = 0.0,
    [property: JsonPropertyName("description")] string Description = "");

public sealed record AiEducationDto(
    [property: JsonPropertyName("degree")] string? Degree = null,
    [property: JsonPropertyName("institution")] string Institution = "",
    [property: JsonPropertyName("field_of_study")] string FieldOfStudy = "",
    [property: JsonPropertyName("graduation_year")] string? GraduationYear = null);

public sealed record AiProjectDto
{
    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; init; } = string.Empty;

    [JsonPropertyName("technologies")]
    public List<string> Technologies { get; init; } = [];

    public AiProjectDto() { }

    [JsonConstructor]
    public AiProjectDto(
        string Name,
        string Description = "",
        List<string>? Technologies = null)
    {
        this.Name = Name;
        this.Description = Description;
        this.Technologies = Technologies ?? [];
    }
}

public sealed record AiStructuredCvDto
{
    [JsonPropertyName("full_name")]
    public string? FullName { get; init; }

    [JsonPropertyName("email")]
    public string? Email { get; init; }

    [JsonPropertyName("phone")]
    public string? Phone { get; init; }

    [JsonPropertyName("career_summary")]
    public string? CareerSummary { get; init; }

    [JsonPropertyName("skills")]
    public List<string> Skills { get; init; } = [];

    [JsonPropertyName("work_experience")]
    public List<AiWorkExperienceDto> WorkExperience { get; init; } = [];

    [JsonPropertyName("education")]
    public List<AiEducationDto> Education { get; init; } = [];

    [JsonPropertyName("certificates")]
    public List<string> Certificates { get; init; } = [];

    [JsonPropertyName("projects")]
    public List<AiProjectDto> Projects { get; init; } = [];

    [JsonPropertyName("technologies")]
    public List<string> Technologies { get; init; } = [];

    public AiStructuredCvDto() { }

    [JsonConstructor]
    public AiStructuredCvDto(
        string? FullName = null,
        string? Email = null,
        string? Phone = null,
        string? CareerSummary = null,
        List<string>? Skills = null,
        List<AiWorkExperienceDto>? WorkExperience = null,
        List<AiEducationDto>? Education = null,
        List<string>? Certificates = null,
        List<AiProjectDto>? Projects = null,
        List<string>? Technologies = null)
    {
        this.FullName = FullName;
        this.Email = Email;
        this.Phone = Phone;
        this.CareerSummary = CareerSummary;
        this.Skills = Skills ?? [];
        this.WorkExperience = WorkExperience ?? [];
        this.Education = Education ?? [];
        this.Certificates = Certificates ?? [];
        this.Projects = Projects ?? [];
        this.Technologies = Technologies ?? [];
    }
}

public sealed record AiStructuredJobDto
{
    [JsonPropertyName("title")]
    public string Title { get; init; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; init; } = string.Empty;

    [JsonPropertyName("required_skills")]
    public List<string> RequiredSkills { get; init; } = [];

    [JsonPropertyName("preferred_skills")]
    public List<string> PreferredSkills { get; init; } = [];

    [JsonPropertyName("minimum_experience_years")]
    public double? MinimumExperienceYears { get; init; }

    [JsonPropertyName("education_requirement")]
    public string? EducationRequirement { get; init; }

    [JsonPropertyName("location")]
    public string? Location { get; init; }

    [JsonPropertyName("salary")]
    public string? Salary { get; init; }

    [JsonPropertyName("employment_type")]
    public string? EmploymentType { get; init; }

    public AiStructuredJobDto() { }

    [JsonConstructor]
    public AiStructuredJobDto(
        string Title,
        string Description = "",
        List<string>? RequiredSkills = null,
        List<string>? PreferredSkills = null,
        double? MinimumExperienceYears = null,
        string? EducationRequirement = null,
        string? Location = null,
        string? Salary = null,
        string? EmploymentType = null)
    {
        this.Title = Title;
        this.Description = Description;
        this.RequiredSkills = RequiredSkills ?? [];
        this.PreferredSkills = PreferredSkills ?? [];
        this.MinimumExperienceYears = MinimumExperienceYears;
        this.EducationRequirement = EducationRequirement;
        this.Location = Location;
        this.Salary = Salary;
        this.EmploymentType = EmploymentType;
    }
}

public sealed record AiMatchRequest(
    [property: JsonPropertyName("cv")] AiStructuredCvDto Cv,
    [property: JsonPropertyName("job")] AiStructuredJobDto Job);

// =============================================================================
// AI Matching Engine Response Contracts (v1)
// Aligned with Python FastAPI MatchResult / ResponseMeta / ErrorResponse
// =============================================================================

public sealed record AiResponseMetaDto(
    [property: JsonPropertyName("algorithm_version")] string AlgorithmVersion = "1.0.0",
    [property: JsonPropertyName("algorithm_variant")] string? AlgorithmVariant = null,
    [property: JsonPropertyName("contract_version")] string? ContractVersion = "match-result-v1",
    [property: JsonPropertyName("schema_version")] string? SchemaVersion = "1.0.0",
    [property: JsonPropertyName("prompt_version")] string? PromptVersion = "v1",
    [property: JsonPropertyName("provider")] string? Provider = null,
    [property: JsonPropertyName("model")] string? Model = null,
    [property: JsonPropertyName("embedding_provider")] string? EmbeddingProvider = null,
    [property: JsonPropertyName("embedding_model")] string? EmbeddingModel = null,
    [property: JsonPropertyName("llm_invoked")] bool? LlmInvoked = null,
    [property: JsonPropertyName("explanation_mode")] string? ExplanationMode = null,
    [property: JsonPropertyName("processing_time_ms")] double ProcessingTimeMs = 0.0,
    [property: JsonPropertyName("correlation_id")] string CorrelationId = "-");

public sealed record AiMatchStrengthDto(
    [property: JsonPropertyName("item")] string Item,
    [property: JsonPropertyName("statement")] string Statement,
    [property: JsonPropertyName("evidence_source")] string EvidenceSource,
    [property: JsonPropertyName("evidence_text")] string? EvidenceText = null);

public sealed record AiMatchGapDto(
    [property: JsonPropertyName("requirement")] string Requirement,
    [property: JsonPropertyName("statement")] string Statement);

public sealed record AiMatchExplanationDto(
    [property: JsonPropertyName("summary")] string Summary,
    [property: JsonPropertyName("strengths")] List<AiMatchStrengthDto>? Strengths = null,
    [property: JsonPropertyName("gaps")] List<AiMatchGapDto>? Gaps = null,
    [property: JsonPropertyName("recommendations")] List<string>? Recommendations = null);

public sealed record AiMatchResultDto
{
    [JsonPropertyName("match_score")]
    public int MatchScore { get; init; }

    [JsonPropertyName("matched_skills")]
    public List<string> MatchedSkills { get; init; } = [];

    [JsonPropertyName("missing_skills")]
    public List<string> MissingSkills { get; init; } = [];

    [JsonPropertyName("experience_comparison")]
    public string ExperienceComparison { get; init; } = string.Empty;

    [JsonPropertyName("education_comparison")]
    public string EducationComparison { get; init; } = string.Empty;

    [JsonPropertyName("project_domain_relevance")]
    public string ProjectDomainRelevance { get; init; } = string.Empty;

    [JsonPropertyName("match_explanation")]
    public string? MatchExplanation { get; init; }

    [JsonPropertyName("explanation_details")]
    public AiMatchExplanationDto? ExplanationDetails { get; init; }

    [JsonPropertyName("status")]
    public string? Status { get; init; }

    [JsonPropertyName("warning")]
    public string? Warning { get; init; }

    [JsonPropertyName("meta")]
    public AiResponseMetaDto Meta { get; init; } = new();

    public AiMatchResultDto() { }

    [JsonConstructor]
    public AiMatchResultDto(
        int MatchScore,
        List<string>? MatchedSkills = null,
        List<string>? MissingSkills = null,
        string ExperienceComparison = "",
        string EducationComparison = "",
        string ProjectDomainRelevance = "",
        string? MatchExplanation = null,
        AiMatchExplanationDto? ExplanationDetails = null,
        string? Status = null,
        string? Warning = null,
        AiResponseMetaDto? Meta = null)
    {
        this.MatchScore = MatchScore;
        this.MatchedSkills = MatchedSkills ?? [];
        this.MissingSkills = MissingSkills ?? [];
        this.ExperienceComparison = ExperienceComparison;
        this.EducationComparison = EducationComparison;
        this.ProjectDomainRelevance = ProjectDomainRelevance;
        this.MatchExplanation = MatchExplanation;
        this.ExplanationDetails = ExplanationDetails;
        this.Status = Status;
        this.Warning = Warning;
        this.Meta = Meta ?? new AiResponseMetaDto();
    }
}

public sealed record AiErrorResponseDto(
    [property: JsonPropertyName("error_code")] string ErrorCode,
    [property: JsonPropertyName("message")] string Message,
    [property: JsonPropertyName("details")] Dictionary<string, object>? Details = null,
    [property: JsonPropertyName("correlation_id")] string CorrelationId = "-");
