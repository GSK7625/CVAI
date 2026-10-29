namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record ExperienceDto(
    string CompanyName,
    string? Position,
    DateOnly StartDate,
    DateOnly? EndDate,
    bool IsCurrent,
    string? Description);
