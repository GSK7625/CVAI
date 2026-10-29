namespace FutureCV.Application.Features.Employer.DTOs;

public sealed record UpdateEmployerInfoRequest(
    string FullName,
    string? Position,
    string? Gender,
    string? Phone);
