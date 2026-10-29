namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record ProjectDto(
    string Name,
    string? Role,
    DateTime? StartDate,
    DateTime? EndDate,
    bool IsCurrent,
    string? ProjectUrl,
    string? Description);

public sealed record ProjectResponse(
    Guid Id,
    string Name,
    string? Role,
    DateTime? StartDate,
    DateTime? EndDate,
    bool IsCurrent,
    string? ProjectUrl,
    string? Description);
