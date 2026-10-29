namespace FutureCV.Application.Features.Employer.DTOs;

public sealed record CreateCompanyRequest(
    string Name,
    string TaxCode,
    string? Scale,
    string? Industry,
    string? WebsiteUrl,
    string? Address,
    string? Description);
