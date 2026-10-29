namespace FutureCV.Application.Common.Models;

/// <summary>
/// Projection representing basic user information from the Identity system,
/// used to decouple the Application layer from ASP.NET Core Identity's AppUser.
/// </summary>
public sealed record IdentityUserInfo(
    Guid Id,
    string Email,
    string? Phone,
    IReadOnlyList<string> Roles,
    bool IsLockedOut,
    DateTimeOffset? LockoutEnd,
    DateTimeOffset CreatedAt);
