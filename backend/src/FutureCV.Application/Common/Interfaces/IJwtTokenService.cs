using System.Security.Claims;
using FutureCV.Application.Common.Models;

namespace FutureCV.Application.Common.Interfaces;

/// <summary>
/// Contract for JWT access token and refresh token generation and validation.
/// </summary>
public interface IJwtTokenService
{
    string GenerateAccessToken(JwtUserInfo user);
    string GenerateRefreshToken();
    string HashRefreshToken(string rawRefreshToken);
    ClaimsPrincipal? GetPrincipalFromExpiredToken(string token);
}
