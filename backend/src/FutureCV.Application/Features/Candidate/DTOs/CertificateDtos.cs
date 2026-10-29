namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record CertificateDto(
    string Name,
    string? Organization,
    DateTime? IssueDate,
    DateTime? ExpirationDate,
    string? CredentialUrl,
    string? Description);

public sealed record CertificateResponse(
    Guid Id,
    string Name,
    string? Organization,
    DateTime? IssueDate,
    DateTime? ExpirationDate,
    string? CredentialUrl,
    string? Description);
