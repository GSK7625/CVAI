namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record CandidateProfileResponse(
    Guid Id,
    Guid UserId,
    string Email,
    string FullName,
    string? Phone,
    string? Address,
    string? AvatarUrl,
    DateTime? DateOfBirth,
    string? Gender,
    string? Summary,
    string? DesiredPosition,
    int? DesiredSalaryMin,
    int? DesiredSalaryMax,
    DateTimeOffset? ProfileUpdatedAt,
    DateTime CreatedAt);

