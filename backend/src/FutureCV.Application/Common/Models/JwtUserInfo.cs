namespace FutureCV.Application.Common.Models;

/// <summary>
/// Pure DTO carrying required data for JWT token generation.
/// Defined in Application layer to keep IJwtTokenService decoupled from Infrastructure (AppUser).
/// </summary>
public sealed record JwtUserInfo(
    Guid UserId,
    string Email,
    IReadOnlyCollection<string> Roles,
    string? SecurityStamp
);
