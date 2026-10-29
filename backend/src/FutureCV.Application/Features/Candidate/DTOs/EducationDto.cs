namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record EducationDto(
    string School,
    string? Degree,
    string? Major,
    int? StartYear,
    int? EndYear,
    string? Description);
