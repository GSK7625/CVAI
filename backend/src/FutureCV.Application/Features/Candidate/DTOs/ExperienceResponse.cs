namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record ExperienceResponse(
    Guid Id,
    string CompanyName,
    string? Position,
    DateOnly StartDate,
    DateOnly? EndDate,
    bool IsCurrent,
    string? Description);
