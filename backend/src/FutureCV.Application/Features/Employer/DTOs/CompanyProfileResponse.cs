namespace FutureCV.Application.Features.Employer.DTOs;

public sealed record CompanyProfileResponse(
    Guid Id,
    string Name,
    string TaxCode,
    string? LogoUrl,
    string? Scale,
    string? Industry,
    string? WebsiteUrl,
    string? Address,
    string? Description,
    string VerifiedStatus,
    DateTimeOffset? VerifiedAt,
    DateTime CreatedAt);
