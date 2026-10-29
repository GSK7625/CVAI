namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record EducationResponse(
    Guid Id,
    string School,
    string? Degree,
    string? Major,
    int? StartYear,
    int? EndYear,
    string? Description);
