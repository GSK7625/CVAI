using FutureCV.Application.Features.Auth.DTOs;
using FutureCV.Application.Features.Auth.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ApiControllerBase
{
    private readonly IAuthService _authService;

    public AuthController(IAuthService authService)
    {
        _authService = authService;
    }

    /// <summary>Register a new Candidate account and automatically log in.</summary>
    [HttpPost("register/candidate")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(AuthResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> RegisterCandidate([FromBody] RegisterCandidateRequest request, CancellationToken cancellationToken)
    {
        var result = await _authService.RegisterCandidateAsync(request, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    /// <summary>Register a new Employer account and automatically log in.</summary>
    [HttpPost("register/employer")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(AuthResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> RegisterEmployer([FromBody] RegisterEmployerRequest request, CancellationToken cancellationToken)
    {
        var result = await _authService.RegisterEmployerAsync(request, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    /// <summary>
    /// Login with email and password.
    /// Returns access token (15 min) and refresh token (7 days).
    /// </summary>
    [HttpPost("login")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(AuthResponse))]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    public async Task<IActionResult> Login([FromBody] LoginRequest request, CancellationToken cancellationToken)
    {
        var result = await _authService.LoginAsync(request, cancellationToken);
        return ToHttpResult(result);
    }

    /// <summary>
    /// Refresh an expired access token using a valid refresh token.
    /// Old refresh token is revoked and a new pair is issued (rotation).
    /// Using a revoked token triggers reuse detection and revokes all sessions.
    /// </summary>
    [HttpPost("refresh")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(AuthResponse))]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> Refresh([FromBody] RefreshTokenRequest? request, CancellationToken cancellationToken)
    {
        var result = await _authService.RefreshTokenAsync(request ?? new RefreshTokenRequest(), cancellationToken);
        return ToHttpResult(result);
    }

    /// <summary>
    /// Logout from the current device by revoking the provided refresh token.
    /// The access token remains valid until it expires (max 15 min).
    /// </summary>
    [HttpPost("logout")]
    [Authorize]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(MessageResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Logout([FromBody] LogoutRequest? request, CancellationToken cancellationToken)
    {
        var userId = GetCurrentUserId();
        if (userId == Guid.Empty) return Unauthorized();

        var result = await _authService.LogoutAsync(userId, request?.RefreshToken, cancellationToken);
        return ToHttpResult(result);
    }

    /// <summary>
    /// Logout from ALL devices by revoking every refresh token for this user.
    /// </summary>
    [HttpPost("logout-all")]
    [Authorize]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(MessageResponse))]
    public async Task<IActionResult> LogoutAll(CancellationToken cancellationToken)
    {
        var userId = GetCurrentUserId();
        if (userId == Guid.Empty) return Unauthorized();

        var result = await _authService.LogoutAllAsync(userId, cancellationToken);
        return ToHttpResult(result);
    }

    /// <summary>
    /// Request a password reset token.
    /// Always returns 200 OK — response does NOT reveal whether the email exists (anti-enumeration).
    /// </summary>
    [HttpPost("forgot-password")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(MessageResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> ForgotPassword([FromBody] ForgotPasswordRequest request, CancellationToken cancellationToken)
    {
        var result = await _authService.ForgotPasswordAsync(request, cancellationToken);
        return ToHttpResult(result);
    }

    /// <summary>
    /// Reset password using the token received via email.
    /// Token expires after 15 minutes.
    /// </summary>
    [HttpPost("reset-password")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(MessageResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> ResetPassword([FromBody] ResetPasswordRequest request, CancellationToken cancellationToken)
    {
        var result = await _authService.ResetPasswordAsync(request, cancellationToken);
        return ToHttpResult(result);
    }

    /// <summary>
    /// Admin endpoint to disable a user account and revoke all their active sessions (BR-07).
    /// </summary>
    [HttpPost("users/{userId:guid}/disable")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(MessageResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DisableUser([FromRoute] Guid userId, CancellationToken cancellationToken)
    {
        var currentAdminId = GetCurrentUserId();
        if (currentAdminId == Guid.Empty) return Unauthorized();

        var result = await _authService.DisableUserAsync(userId, currentAdminId, cancellationToken);
        return ToHttpResult(result);
    }

    /// <summary>
    /// Admin endpoint to re-enable a previously disabled user account.
    /// </summary>
    [HttpPost("users/{userId:guid}/enable")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(MessageResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> EnableUser([FromRoute] Guid userId, CancellationToken cancellationToken)
    {
        var result = await _authService.EnableUserAsync(userId, cancellationToken);
        return ToHttpResult(result);
    }

    /// <summary>Log in using Google ID Token.</summary>
    [HttpPost("google/login")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(AuthResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> GoogleLogin([FromBody] GoogleLoginRequest request, CancellationToken cancellationToken)
    {
        var result = await _authService.GoogleLoginAsync(request, cancellationToken);
        return ToHttpResult(result);
    }

    /// <summary>Register a Candidate using Google ID Token.</summary>
    [HttpPost("google/register/candidate")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(AuthResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> GoogleRegisterCandidate([FromBody] GoogleLoginRequest request, CancellationToken cancellationToken)
    {
        var result = await _authService.GoogleRegisterCandidateAsync(request, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    /// <summary>Register an Employer using Google ID Token and additional profile data.</summary>
    [HttpPost("google/register/employer")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(AuthResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> GoogleRegisterEmployer([FromBody] GoogleRegisterEmployerRequest request, CancellationToken cancellationToken)
    {
        var result = await _authService.GoogleRegisterEmployerAsync(request, cancellationToken);
        return ToHttpResult(result, created: true);
    }
}
