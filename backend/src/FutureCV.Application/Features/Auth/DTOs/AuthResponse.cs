namespace FutureCV.Application.Features.Auth.DTOs;

public record AuthResponse(
    string AccessToken,
    DateTimeOffset AccessTokenExpiresAt,
    string RefreshToken,
    string Role,
    IReadOnlyList<string> Roles
);
