namespace FutureCV.Application.Features.Employer.DTOs;

public sealed record UpdateCompanyInfoRequest(
    string Name,
    string? Scale,
    string? Industry,
    string? WebsiteUrl,
    string? Address,
    string? Description);
