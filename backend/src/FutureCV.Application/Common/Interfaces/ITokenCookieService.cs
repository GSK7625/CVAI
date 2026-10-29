namespace FutureCV.Application.Common.Interfaces;

/// <summary>
/// Abstraction for managing authentication cookies (e.g. refresh token).
/// Keeps Application layer decoupled from ASP.NET Core HttpContext.
/// </summary>
public interface ITokenCookieService
{
    /// <summary>Appends the refresh token to the HTTP response as a secure, HttpOnly cookie.</summary>
    void SetRefreshToken(string refreshToken);

    /// <summary>Deletes the refresh token cookie from the HTTP response.</summary>
    void DeleteRefreshToken();

    /// <summary>Retrieves the refresh token from the HTTP request cookie, if present.</summary>
    string? GetRefreshToken();
}
