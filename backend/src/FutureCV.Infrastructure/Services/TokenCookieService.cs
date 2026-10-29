using FutureCV.Application.Common.Interfaces;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;

namespace FutureCV.Infrastructure.Services;

/// <summary>
/// Implementation of ITokenCookieService using ASP.NET Core IHttpContextAccessor.
/// </summary>
public class TokenCookieService : ITokenCookieService
{
    private const string RefreshTokenCookieName = "refreshToken";

    private readonly IHttpContextAccessor _httpContextAccessor;
    private readonly IConfiguration _configuration;

    public TokenCookieService(
        IHttpContextAccessor httpContextAccessor,
        IConfiguration configuration)
    {
        _httpContextAccessor = httpContextAccessor;
        _configuration = configuration;
    }

    public void SetRefreshToken(string refreshToken)
    {
        var response = _httpContextAccessor.HttpContext?.Response;
        if (response == null) return;

        var request = _httpContextAccessor.HttpContext?.Request;
        var isHttps = request?.IsHttps ?? false;

        var expiryDays = int.TryParse(_configuration["Jwt:RefreshTokenExpiryDays"], out var d) ? d : 7;

        var cookieOptions = new CookieOptions
        {
            HttpOnly = true,
            Secure = isHttps,
            SameSite = isHttps ? SameSiteMode.None : SameSiteMode.Lax,
            Expires = DateTimeOffset.UtcNow.AddDays(expiryDays),
            Path = "/"
        };

        response.Cookies.Append(RefreshTokenCookieName, refreshToken, cookieOptions);
    }

    public void DeleteRefreshToken()
    {
        var response = _httpContextAccessor.HttpContext?.Response;
        if (response == null) return;

        var request = _httpContextAccessor.HttpContext?.Request;
        var isHttps = request?.IsHttps ?? false;

        var cookieOptions = new CookieOptions
        {
            HttpOnly = true,
            Secure = isHttps,
            SameSite = isHttps ? SameSiteMode.None : SameSiteMode.Lax,
            Path = "/"
        };

        response.Cookies.Delete(RefreshTokenCookieName, cookieOptions);
    }

    public string? GetRefreshToken()
    {
        return _httpContextAccessor.HttpContext?.Request.Cookies[RefreshTokenCookieName];
    }
}
