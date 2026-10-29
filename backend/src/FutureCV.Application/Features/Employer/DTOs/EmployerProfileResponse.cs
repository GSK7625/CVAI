namespace FutureCV.Application.Features.Employer.DTOs;

public sealed record EmployerProfileResponse(
    Guid Id,
    Guid UserId,
    string FullName,
    string? Position,
    string? Gender,
    string? Phone,
    string? AvatarUrl,
    Guid CompanyId,
    DateTime CreatedAt);
