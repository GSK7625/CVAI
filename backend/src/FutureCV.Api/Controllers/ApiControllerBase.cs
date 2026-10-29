using FutureCV.Application.Common.Models;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Controllers;

/// <summary>
/// Shared base for all API controllers.
/// Provides helpers for extracting user identity and mapping ServiceResult to HTTP responses.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public abstract class ApiControllerBase : ControllerBase
{
    // Allowed MIME types and extensions for avatar upload
    protected static readonly string[] AvatarAllowedMimeTypes = ["image/jpeg", "image/png"];
    protected static readonly string[] AvatarAllowedExtensions = [".jpg", ".jpeg", ".png"];
    protected const long AvatarMaxSizeBytes = 5 * 1024 * 1024; // 5 MB

    // Maps ServiceErrorType → HTTP status code
    // Extend this method when new error types are introduced
    protected IActionResult ToHttpResult<T>(ServiceResult<T> result, bool created = false)
    {
        if (result.IsSuccess)
            return created ? StatusCode(201, result.Data) : Ok(result.Data);

        return result.ErrorType switch
        {
            ServiceErrorType.NotFound        => NotFound(new { message = result.ErrorMessage }),
            ServiceErrorType.Unauthorized    => Unauthorized(new { message = result.ErrorMessage }),
            ServiceErrorType.Forbidden       => StatusCode(403, new { message = result.ErrorMessage }),
            ServiceErrorType.Conflict        => Conflict(new { message = result.ErrorMessage }),
            ServiceErrorType.Infrastructure  => StatusCode(500, new { message = result.ErrorMessage }),
            _                                => BadRequest(new { message = result.ErrorMessage }),
        };
    }

    // Extracts the authenticated user's Guid from JWT NameIdentifier claim
    protected Guid GetCurrentUserId()
    {
        var claim = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
        return Guid.TryParse(claim, out var id) ? id : Guid.Empty;
    }

    // Validates avatar file format and size — call at controller level before hitting service
    protected IActionResult? ValidateAvatarFile(IFormFile file)
    {
        var extension = Path.GetExtension(file.FileName).ToLowerInvariant();
        if (!AvatarAllowedExtensions.Contains(extension))
            return BadRequest(new { message = "Avatar must be a JPG or PNG file." });

        if (!AvatarAllowedMimeTypes.Contains(file.ContentType.ToLowerInvariant()))
            return BadRequest(new { message = "Avatar must be a JPG or PNG file." });

        if (file.Length > AvatarMaxSizeBytes)
            return BadRequest(new { message = "Avatar file size must not exceed 5 MB." });

        return null; // null = valid
    }

    // Helper to get client IP address for audit logging
    protected string? GetClientIpAddress()
    {
        return HttpContext.Connection.RemoteIpAddress?.ToString();
    }
}

