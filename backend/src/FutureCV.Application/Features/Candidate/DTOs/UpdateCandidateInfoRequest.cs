namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record UpdateCandidateInfoRequest(
    string FullName,
    string? Phone,
    string? Address,
    DateTime? DateOfBirth,
    string? Gender,
    string? Summary,
    string? DesiredPosition,
    int? DesiredSalaryMin,
    int? DesiredSalaryMax);
