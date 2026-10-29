namespace FutureCV.Application.Features.Candidate.DTOs;

// -----------------------------------------------------------------------------
// Structured CV Data Models (P2-UC04)
// -----------------------------------------------------------------------------

public sealed record CvExperienceDto(
    string CompanyName,
    string? Position,
    DateOnly StartDate,
    DateOnly? EndDate,
    bool IsCurrent,
    string? Description);

public sealed record CvEducationDto(
    string School,
    string? Degree,
    string? Major,
    int? StartYear,
    int? EndYear,
    string? Description);

public sealed record CvProjectDto(
    string Name,
    string? Role,
    DateTime? StartDate,
    DateTime? EndDate,
    bool IsCurrent,
    string? Description,
    string? Technologies);

public sealed record StructuredCvDataDto(
    string FullName,
    string? Email,
    string? Phone,
    string? Summary,
    List<string> Skills,
    List<CvExperienceDto> Experiences,
    List<CvEducationDto> Educations,
    List<CvProjectDto> Projects);

public sealed record CvStructuredDataResponse(
    Guid CvId,
    string? Title,
    string? FileUrl,
    string ParseStatus,
    bool IsVerifiedByUser,
    DateTime? VerifiedAt,
    StructuredCvDataDto Data,
    string? RawText);

public sealed record UpdateStructuredCvDataRequest(
    StructuredCvDataDto Data);

// -----------------------------------------------------------------------------
// CV Evaluation & Analysis Models (P2-UC05, P2-UC06)
// -----------------------------------------------------------------------------

public sealed record CvAnalysisResponse(
    Guid CvId,
    int CvScore,
    IReadOnlyList<string> Strengths,
    IReadOnlyList<string> Weaknesses,
    IReadOnlyList<string> Improvements,
    IReadOnlyList<string> MissingSkills,
    string ModelVersion,
    DateTime GeneratedAt);

// -----------------------------------------------------------------------------
// AI Integration Webhook Request (For future Python FastAPI callback)
// -----------------------------------------------------------------------------

public sealed record AiCvCallbackRequest(
    string? RawText,
    StructuredCvDataDto? StructuredData,
    int? CvScore,
    List<string>? Strengths,
    List<string>? Weaknesses,
    List<string>? Improvements,
    List<string>? MissingSkills,
    string? ErrorMessage);
