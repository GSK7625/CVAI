using System.IdentityModel.Tokens.Jwt;
using FluentValidation;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Auth.DTOs;
using FutureCV.Application.Features.Auth.Interfaces;
using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;

namespace FutureCV.Infrastructure.Identity;

/// <summary>
/// Implementation of IAuthService for user authentication, registration, password reset,
/// and refresh token lifecycle management. Uses FluentValidation for request validation.
/// </summary>
public class AuthService : IAuthService
{
    private readonly UserManager<AppUser> _userManager;
    private readonly RoleManager<IdentityRole<Guid>> _roleManager;
    private readonly IApplicationDbContext _context;
    private readonly IJwtTokenService _jwtTokenService;
    private readonly IConfiguration _configuration;
    private readonly IEmailService _emailService;
    private readonly IGoogleTokenValidator _googleTokenValidator;
    private readonly IValidator<RegisterCandidateRequest> _registerCandidateValidator;
    private readonly IValidator<RegisterEmployerRequest> _registerEmployerValidator;
    private readonly IValidator<LoginRequest> _loginValidator;
    private readonly IValidator<RefreshTokenRequest> _refreshTokenValidator;
    private readonly IValidator<ForgotPasswordRequest> _forgotPasswordValidator;
    private readonly IValidator<ResetPasswordRequest> _resetPasswordValidator;
    private readonly IValidator<GoogleLoginRequest> _googleLoginValidator;
    private readonly IValidator<GoogleRegisterEmployerRequest> _googleRegisterEmployerValidator;
    private readonly ITokenCookieService _tokenCookieService;

    public AuthService(
        UserManager<AppUser> userManager,
        RoleManager<IdentityRole<Guid>> roleManager,
        IApplicationDbContext context,
        IJwtTokenService jwtTokenService,
        IConfiguration configuration,
        IEmailService emailService,
        IGoogleTokenValidator googleTokenValidator,
        ITokenCookieService tokenCookieService,
        IValidator<RegisterCandidateRequest> registerCandidateValidator,
        IValidator<RegisterEmployerRequest> registerEmployerValidator,
        IValidator<LoginRequest> loginValidator,
        IValidator<RefreshTokenRequest> refreshTokenValidator,
        IValidator<ForgotPasswordRequest> forgotPasswordValidator,
        IValidator<ResetPasswordRequest> resetPasswordValidator,
        IValidator<GoogleLoginRequest> googleLoginValidator,
        IValidator<GoogleRegisterEmployerRequest> googleRegisterEmployerValidator)
    {
        _userManager = userManager;
        _roleManager = roleManager;
        _context = context;
        _jwtTokenService = jwtTokenService;
        _configuration = configuration;
        _emailService = emailService;
        _googleTokenValidator = googleTokenValidator;
        _tokenCookieService = tokenCookieService;
        _registerCandidateValidator = registerCandidateValidator;
        _registerEmployerValidator = registerEmployerValidator;
        _loginValidator = loginValidator;
        _refreshTokenValidator = refreshTokenValidator;
        _forgotPasswordValidator = forgotPasswordValidator;
        _resetPasswordValidator = resetPasswordValidator;
        _googleLoginValidator = googleLoginValidator;
        _googleRegisterEmployerValidator = googleRegisterEmployerValidator;
    }

    public async Task<ServiceResult<AuthResponse>> RegisterCandidateAsync(
        RegisterCandidateRequest request,
        CancellationToken cancellationToken = default)
    {
        var validationResult = await _registerCandidateValidator.ValidateAsync(request, cancellationToken);
        if (!validationResult.IsValid)
        {
            var errors = string.Join(" ", validationResult.Errors.Select(e => e.ErrorMessage));
            return ServiceResult.Failure<AuthResponse>(errors);
        }

        var targetRole = "Candidate";

        // Ensure role exists in DB
        if (!await _roleManager.RoleExistsAsync(targetRole))
        {
            return ServiceResult.InfrastructureError<AuthResponse>(
                $"Role '{targetRole}' is not initialized in the system.");
        }

        using var transaction = await _context.Database.BeginTransactionAsync(cancellationToken);
        try
        {
            // Check existing user for multi-role support
            var existingUser = await _userManager.FindByEmailAsync(request.Email);
            if (existingUser is not null)
            {
                if (existingUser.IsDeleted)
                    return ServiceResult.Forbidden<AuthResponse>("Tài khoản đã bị vô hiệu hóa.");

                var isPasswordValid = await _userManager.CheckPasswordAsync(existingUser, request.Password);
                if (!isPasswordValid)
                    return ServiceResult.Failure<AuthResponse>("Mật khẩu không đúng cho tài khoản đã tồn tại.");

                if (await _userManager.IsInRoleAsync(existingUser, targetRole))
                    return ServiceResult.Conflict<AuthResponse>("ACCOUNT_ALREADY_EXISTS");

                // Add Candidate role & profile to existing user
                await _userManager.AddToRoleAsync(existingUser, targetRole);
                var newCandidate = new Candidate
                {
                    UserId = existingUser.Id,
                    FullName = request.FullName
                };
                _context.Candidates.Add(newCandidate);

                var existingAuthResponse = await GenerateAuthTokensAsync(existingUser, targetRole, cancellationToken);
                await _context.SaveChangesAsync(cancellationToken);
                await transaction.CommitAsync(cancellationToken);

                return ServiceResult.Success(existingAuthResponse);
            }

            var user = new AppUser
            {
                Id = Guid.NewGuid(),
                UserName = request.Email,
                Email = request.Email,
                CreatedAt = DateTimeOffset.UtcNow,
                UpdatedAt = DateTimeOffset.UtcNow,
                IsDeleted = false
            };

            var createResult = await _userManager.CreateAsync(user, request.Password);
            if (!createResult.Succeeded)
            {
                var errors = string.Join(" ", createResult.Errors.Select(e => e.Description));
                return ServiceResult.Failure<AuthResponse>(errors);
            }

            var roleResult = await _userManager.AddToRoleAsync(user, targetRole);
            if (!roleResult.Succeeded)
            {
                var errors = string.Join(" ", roleResult.Errors.Select(e => e.Description));
                return ServiceResult.Failure<AuthResponse>(errors);
            }

            var candidate = new Candidate
            {
                UserId = user.Id,
                FullName = request.FullName
            };
            _context.Candidates.Add(candidate);

            var authResponse = await GenerateAuthTokensAsync(user, targetRole, cancellationToken);
            await _context.SaveChangesAsync(cancellationToken);

            await transaction.CommitAsync(cancellationToken);

            return ServiceResult.Success(authResponse);
        }
        catch (DbUpdateException)
        {
            await transaction.RollbackAsync(cancellationToken);
            return ServiceResult.Conflict<AuthResponse>("ACCOUNT_ALREADY_EXISTS");
        }
        catch (Exception)
        {
            await transaction.RollbackAsync(cancellationToken);
            return ServiceResult.InfrastructureError<AuthResponse>(
                "Registration failed due to a system error. Please try again.");
        }
    }

    public async Task<ServiceResult<AuthResponse>> RegisterEmployerAsync(
        RegisterEmployerRequest request,
        CancellationToken cancellationToken = default)
    {
        var validationResult = await _registerEmployerValidator.ValidateAsync(request, cancellationToken);
        if (!validationResult.IsValid)
        {
            var errors = string.Join(" ", validationResult.Errors.Select(e => e.ErrorMessage));
            return ServiceResult.Failure<AuthResponse>(errors);
        }

        var targetRole = "Employer";

        if (!await _roleManager.RoleExistsAsync(targetRole))
        {
            return ServiceResult.InfrastructureError<AuthResponse>(
                $"Role '{targetRole}' is not initialized in the system.");
        }

        using var transaction = await _context.Database.BeginTransactionAsync(cancellationToken);
        try
        {
            // Check existing user for multi-role support
            var existingUser = await _userManager.FindByEmailAsync(request.Email);
            if (existingUser is not null)
            {
                if (existingUser.IsDeleted)
                    return ServiceResult.Forbidden<AuthResponse>("Tài khoản đã bị vô hiệu hóa.");

                var isPasswordValid = await _userManager.CheckPasswordAsync(existingUser, request.Password);
                if (!isPasswordValid)
                    return ServiceResult.Failure<AuthResponse>("Mật khẩu không đúng cho tài khoản đã tồn tại.");

                if (await _userManager.IsInRoleAsync(existingUser, targetRole))
                    return ServiceResult.Conflict<AuthResponse>("ACCOUNT_ALREADY_EXISTS");

                // Add Employer role & profile to existing user
                await _userManager.AddToRoleAsync(existingUser, targetRole);

                var company = new Company
                {
                    Name = request.CompanyName,
                    TaxCode = "TEMP_" + Guid.NewGuid().ToString("N")[..8],
                    VerifiedStatus = CompanyVerificationStatus.Pending
                };
                _context.Companies.Add(company);
                await _context.SaveChangesAsync(cancellationToken);

                var employer = new Employer
                {
                    UserId = existingUser.Id,
                    FullName = request.FullName,
                    Phone = request.Phone,
                    CompanyId = company.Id
                };
                _context.Employers.Add(employer);

                var existingAuthResponse = await GenerateAuthTokensAsync(existingUser, targetRole, cancellationToken);
                await _context.SaveChangesAsync(cancellationToken);
                await transaction.CommitAsync(cancellationToken);

                return ServiceResult.Success(existingAuthResponse);
            }

            var user = new AppUser
            {
                Id = Guid.NewGuid(),
                UserName = request.Email,
                Email = request.Email,
                CreatedAt = DateTimeOffset.UtcNow,
                UpdatedAt = DateTimeOffset.UtcNow,
                IsDeleted = false
            };

            var createResult = await _userManager.CreateAsync(user, request.Password);
            if (!createResult.Succeeded)
            {
                var errors = string.Join(" ", createResult.Errors.Select(e => e.Description));
                return ServiceResult.Failure<AuthResponse>(errors);
            }

            var roleResult = await _userManager.AddToRoleAsync(user, targetRole);
            if (!roleResult.Succeeded)
            {
                var errors = string.Join(" ", roleResult.Errors.Select(e => e.Description));
                return ServiceResult.Failure<AuthResponse>(errors);
            }

            // Create Company
            var newCompany = new Company
            {
                Name = request.CompanyName,
                TaxCode = "TEMP_" + Guid.NewGuid().ToString("N")[..8],
                VerifiedStatus = CompanyVerificationStatus.Pending
            };
            _context.Companies.Add(newCompany);
            await _context.SaveChangesAsync(cancellationToken);

            // Create Employer
            var newEmployer = new Employer
            {
                UserId = user.Id,
                FullName = request.FullName,
                Phone = request.Phone,
                CompanyId = newCompany.Id
            };
            _context.Employers.Add(newEmployer);

            var authResponse = await GenerateAuthTokensAsync(user, targetRole, cancellationToken);
            await _context.SaveChangesAsync(cancellationToken);

            await transaction.CommitAsync(cancellationToken);

            return ServiceResult.Success(authResponse);
        }
        catch (DbUpdateException)
        {
            await transaction.RollbackAsync(cancellationToken);
            return ServiceResult.Conflict<AuthResponse>("ACCOUNT_ALREADY_EXISTS");
        }
        catch (Exception)
        {
            await transaction.RollbackAsync(cancellationToken);
            return ServiceResult.InfrastructureError<AuthResponse>(
                "Registration failed due to a system error. Please try again.");
        }
    }

    public async Task<ServiceResult<AuthResponse>> LoginAsync(
        LoginRequest request,
        CancellationToken cancellationToken = default)
    {
        var validationResult = await _loginValidator.ValidateAsync(request, cancellationToken);
        if (!validationResult.IsValid)
        {
            var errors = string.Join(" ", validationResult.Errors.Select(e => e.ErrorMessage));
            return ServiceResult.Failure<AuthResponse>(errors);
        }

        // Always return 401 on missing user (avoid email enumeration)
        var user = await _userManager.FindByEmailAsync(request.Email);
        if (user is null)
            return ServiceResult.Unauthorized<AuthResponse>("Invalid email or password.");

        // Check soft-delete (admin disabled) before password check
        if (user.IsDeleted)
            return ServiceResult.Forbidden<AuthResponse>("Account has been disabled. Please contact support.");

        // Check lockout (may have been locked by previous failed attempts)
        if (await _userManager.IsLockedOutAsync(user))
        {
            var until = user.LockoutEnd?.ToString("o") ?? "a while";
            return ServiceResult.Forbidden<AuthResponse>(
                $"Account is locked until {until}. Please try again later.");
        }

        // Verify password
        var passwordValid = await _userManager.CheckPasswordAsync(user, request.Password);
        if (!passwordValid)
        {
            // Increment AccessFailedCount — Identity enforces lockout automatically
            await _userManager.AccessFailedAsync(user);

            // Re-check lockout after failure
            if (await _userManager.IsLockedOutAsync(user))
            {
                var until = user.LockoutEnd?.ToString("o") ?? "a while";
                return ServiceResult.Forbidden<AuthResponse>(
                    $"Too many failed attempts. Account is locked until {until}.");
            }

            return ServiceResult.Unauthorized<AuthResponse>("Invalid email or password.");
        }

        // Success — reset failed count
        await _userManager.ResetAccessFailedCountAsync(user);

        var authResponse = await GenerateAuthTokensAsync(user, role: null, cancellationToken);
        await _context.SaveChangesAsync(cancellationToken);

        return ServiceResult.Success(authResponse);
    }

    public async Task<ServiceResult<AuthResponse>> RefreshTokenAsync(
        RefreshTokenRequest request,
        CancellationToken cancellationToken = default)
    {
        var validationResult = await _refreshTokenValidator.ValidateAsync(request, cancellationToken);
        if (!validationResult.IsValid)
        {
            var errors = string.Join(" ", validationResult.Errors.Select(e => e.ErrorMessage));
            return ServiceResult.Failure<AuthResponse>(errors);
        }

        // 1. Look up stored refresh token by hash (from request body or cookie)
        var rawToken = !string.IsNullOrWhiteSpace(request?.RefreshToken)
            ? request.RefreshToken
            : _tokenCookieService.GetRefreshToken();

        if (string.IsNullOrWhiteSpace(rawToken))
            return ServiceResult.Unauthorized<AuthResponse>("Refresh token is required.");

        var tokenHash = _jwtTokenService.HashRefreshToken(rawToken);
        var storedToken = await _context.RefreshTokens
            .FirstOrDefaultAsync(t => t.TokenHash == tokenHash, cancellationToken);

        if (storedToken is null)
            return ServiceResult.Unauthorized<AuthResponse>("Invalid or expired refresh token.");

        var userId = storedToken.UserId;

        // 2. Load user and check account status
        var user = await _userManager.FindByIdAsync(userId.ToString());
        if (user is null || user.IsDeleted)
            return ServiceResult.Forbidden<AuthResponse>("Account has been disabled.");

        // REUSE DETECTION: token was already revoked → possible token theft
        if (storedToken.IsRevoked)
        {
            var allActive = await _context.RefreshTokens
                .Where(t => t.UserId == userId && t.RevokedAt == null)
                .ToListAsync(cancellationToken);
            foreach (var t in allActive)
                t.RevokedAt = DateTimeOffset.UtcNow;
            await _context.SaveChangesAsync(cancellationToken);

            _tokenCookieService.DeleteRefreshToken();

            return ServiceResult.Unauthorized<AuthResponse>(
                "Refresh token has already been used. All sessions revoked for security.");
        }

        if (storedToken.IsExpired)
        {
            _tokenCookieService.DeleteRefreshToken();
            return ServiceResult.Unauthorized<AuthResponse>("Refresh token has expired. Please log in again.");
        }

        // Build new token pair
        var roles = await _userManager.GetRolesAsync(user);
        var jwtInfo = new JwtUserInfo(
            UserId: user.Id,
            Email: user.Email!,
            Roles: roles.AsReadOnly(),
            SecurityStamp: user.SecurityStamp);

        var newAccessToken = _jwtTokenService.GenerateAccessToken(jwtInfo);
        var expiryMinutes = int.TryParse(_configuration["Jwt:AccessTokenExpiryMinutes"], out var m) ? m : 15;
        var accessTokenExpiresAt = DateTimeOffset.UtcNow.AddMinutes(expiryMinutes);

        var newRawRefreshToken = _jwtTokenService.GenerateRefreshToken();
        var newTokenHash = _jwtTokenService.HashRefreshToken(newRawRefreshToken);
        var expiryDays = int.TryParse(_configuration["Jwt:RefreshTokenExpiryDays"], out var d) ? d : 7;

        var newRefreshToken = new RefreshToken
        {
            Id = Guid.NewGuid(),
            UserId = user.Id,
            TokenHash = newTokenHash,
            ExpiresAt = DateTimeOffset.UtcNow.AddDays(expiryDays),
            CreatedAt = DateTimeOffset.UtcNow
        };

        // Rotate: revoke old, link to new
        storedToken.RevokedAt = DateTimeOffset.UtcNow;
        storedToken.ReplacedByTokenId = newRefreshToken.Id;

        _context.RefreshTokens.Add(newRefreshToken);
        await _context.SaveChangesAsync(cancellationToken);

        // Update cookie with rotated refresh token
        _tokenCookieService.SetRefreshToken(newRawRefreshToken);

        var primaryRole = roles.Contains("Admin")
            ? "Admin"
            : roles.Contains("Employer")
                ? "Employer"
                : roles.FirstOrDefault() ?? string.Empty;

        return ServiceResult.Success(new AuthResponse(
            AccessToken: newAccessToken,
            AccessTokenExpiresAt: accessTokenExpiresAt,
            RefreshToken: newRawRefreshToken,
            Role: primaryRole,
            Roles: roles.ToList().AsReadOnly()));
    }

    public async Task<ServiceResult<MessageResponse>> LogoutAsync(
        Guid userId,
        string? refreshToken = null,
        CancellationToken cancellationToken = default)
    {
        var rawToken = !string.IsNullOrWhiteSpace(refreshToken)
            ? refreshToken
            : _tokenCookieService.GetRefreshToken();

        // Always delete cookie on logout
        _tokenCookieService.DeleteRefreshToken();

        if (string.IsNullOrWhiteSpace(rawToken))
            return ServiceResult.Success(new MessageResponse("Logged out."));

        var tokenHash = _jwtTokenService.HashRefreshToken(rawToken);
        var storedToken = await _context.RefreshTokens
            .FirstOrDefaultAsync(t => t.TokenHash == tokenHash && t.UserId == userId, cancellationToken);

        // Idempotent: already revoked or not found — still return success
        if (storedToken is not null && !storedToken.IsRevoked)
        {
            storedToken.RevokedAt = DateTimeOffset.UtcNow;
            await _context.SaveChangesAsync(cancellationToken);
        }

        return ServiceResult.Success(new MessageResponse("Logged out."));
    }

    public async Task<ServiceResult<MessageResponse>> LogoutAllAsync(
        Guid userId,
        CancellationToken cancellationToken = default)
    {
        // Always delete cookie on logout
        _tokenCookieService.DeleteRefreshToken();

        var activeTokens = await _context.RefreshTokens
            .Where(t => t.UserId == userId && t.RevokedAt == null)
            .ToListAsync(cancellationToken);

        foreach (var token in activeTokens)
            token.RevokedAt = DateTimeOffset.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        return ServiceResult.Success(new MessageResponse("Logged out from all devices."));
    }

    public async Task<ServiceResult<MessageResponse>> ForgotPasswordAsync(
        ForgotPasswordRequest request,
        CancellationToken cancellationToken = default)
    {
        var validationResult = await _forgotPasswordValidator.ValidateAsync(request, cancellationToken);
        if (!validationResult.IsValid)
        {
            var errors = string.Join(" ", validationResult.Errors.Select(e => e.ErrorMessage));
            return ServiceResult.Failure<MessageResponse>(errors);
        }

        // Always return 200 — never reveal whether the email exists (anti-enumeration)
        var user = await _userManager.FindByEmailAsync(request.Email);
        if (user is null || user.IsDeleted)
        {
            return ServiceResult.Success(
                new MessageResponse("If the email exists, a reset link has been sent."));
        }

        var token = await _userManager.GeneratePasswordResetTokenAsync(user);

        // Build reset link for Frontend
        var frontendUrl = _configuration["FrontendUrl"] ?? "http://localhost:3000";
        var resetLink =
            $"{frontendUrl}/reset-password?email={Uri.EscapeDataString(user.Email!)}&token={Uri.EscapeDataString(token)}";

        var htmlBody = $@"
            <div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;'>
                <h2 style='color: #333;'>FutureCV - Đặt lại mật khẩu</h2>
                <p>Xin chào,</p>
                <p>Bạn đã gửi yêu cầu đặt lại mật khẩu cho tài khoản <strong>{user.Email}</strong>.</p>
                <p>Vui lòng nhấp vào nút bên dưới để tiến hành đặt lại mật khẩu (Link có hiệu lực trong 15 phút):</p>
                <p style='margin: 30px 0;'>
                    <a href='{resetLink}' style='background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;'>Đặt lại mật khẩu</a>
                </p>
                <p style='color: #666; font-size: 12px;'>Nếu nút bấm không hoạt động, hãy copy đường dẫn sau vào trình duyệt:</p>
                <p style='color: #666; font-size: 12px;'>{resetLink}</p>
                <hr style='border: none; border-top: 1px solid #eee; margin: 20px 0;' />
                <p style='color: #999; font-size: 12px;'>Nếu bạn không yêu cầu hành động này, vui lòng bỏ qua email này.</p>
            </div>";

        try
        {
            await _emailService.SendEmailAsync(user.Email!, "FutureCV - Yêu cầu đặt lại mật khẩu", htmlBody,
                cancellationToken);
        }
        catch
        {
            // Log exception in production if email fails, but return anti-enumeration response
        }

        return ServiceResult.Success(
            new MessageResponse("If the email exists, a reset link has been sent."));
    }

    public async Task<ServiceResult<MessageResponse>> ResetPasswordAsync(
        ResetPasswordRequest request,
        CancellationToken cancellationToken = default)
    {
        var validationResult = await _resetPasswordValidator.ValidateAsync(request, cancellationToken);
        if (!validationResult.IsValid)
        {
            var errors = string.Join(" ", validationResult.Errors.Select(e => e.ErrorMessage));
            return ServiceResult.Failure<MessageResponse>(errors);
        }

        // Return generic error for both "user not found" and "invalid token"
        // to prevent user enumeration via the reset endpoint
        var user = await _userManager.FindByEmailAsync(request.Email);
        if (user is null || user.IsDeleted)
        {
            return ServiceResult.Failure<MessageResponse>("Invalid or expired reset token.");
        }

        // 1. Decode URL-encoded characters (like %2F -> /, %2B -> +) if user copied raw from URL
        var decodedToken = Uri.UnescapeDataString(request.Token);

        // 2. Normalize token in case '+' characters were converted to spaces in URL / JSON decoding
        var normalizedToken = decodedToken.Replace(" ", "+");

        var result = await _userManager.ResetPasswordAsync(user, normalizedToken, request.NewPassword);
        if (!result.Succeeded)
        {
            var isTokenError = result.Errors.Any(e => e.Code == "InvalidToken");
            if (isTokenError)
            {
                // Mask only token errors for security
                return ServiceResult.Failure<MessageResponse>("Invalid or expired reset token.");
            }

            // It's likely a password policy error (e.g., missing uppercase, special char, etc.)
            var errors = string.Join(" ", result.Errors.Select(e => e.Description));
            return ServiceResult.Failure<MessageResponse>(errors);
        }

        // Explicit unlock — deterministic recovery, independent of ASP.NET Identity internal behavior.
        // If unlock fails: password reset is already complete; do not rollback.
        _ = await _userManager.SetLockoutEndDateAsync(user, null);
        _ = await _userManager.ResetAccessFailedCountAsync(user);

        // Rotate SecurityStamp — invalidates ALL existing JWT + refresh tokens for this user
        _ = await _userManager.UpdateSecurityStampAsync(user);

        return ServiceResult.Success(
            new MessageResponse("Password reset successful. You can now log in with your new password."));
    }

    public async Task<ServiceResult<MessageResponse>> DisableUserAsync(
        Guid targetUserId,
        Guid currentAdminId,
        CancellationToken cancellationToken = default)
    {
        var user = await _userManager.FindByIdAsync(targetUserId.ToString());
        if (user is null)
        {
            return ServiceResult.NotFound<MessageResponse>("User not found.");
        }

        // Guard 1: Admin cannot disable their own account
        if (targetUserId == currentAdminId)
        {
            return ServiceResult.Failure<MessageResponse>(
                "Cannot disable an active Admin account.");
        }

        // Guard 2: Cannot disable any account with the Admin role
        if (await _userManager.IsInRoleAsync(user, "Admin"))
        {
            return ServiceResult.Failure<MessageResponse>(
                "Cannot disable a system Admin account.");
        }

        user.IsDeleted = true;
        user.UpdatedAt = DateTimeOffset.UtcNow;

        // Verify IdentityResult — do not assume UpdateAsync always succeeds
        var updateResult = await _userManager.UpdateAsync(user);
        if (!updateResult.Succeeded)
        {
            return ServiceResult.InfrastructureError<MessageResponse>(
                string.Join("; ", updateResult.Errors.Select(e => e.Description)));
        }

        // Revoke all active refresh tokens immediately (BR-07 / Session Invalidation)
        var activeTokens = await _context.RefreshTokens
            .Where(t => t.UserId == targetUserId && t.RevokedAt == null)
            .ToListAsync(cancellationToken);

        foreach (var token in activeTokens)
        {
            token.RevokedAt = DateTimeOffset.UtcNow;
        }

        await _context.SaveChangesAsync(cancellationToken);

        return ServiceResult.Success(
            new MessageResponse("User account has been disabled and all active sessions were revoked."));
    }

    public async Task<ServiceResult<MessageResponse>> EnableUserAsync(
        Guid userId,
        CancellationToken cancellationToken = default)
    {
        var user = await _userManager.FindByIdAsync(userId.ToString());
        if (user is null)
        {
            return ServiceResult.NotFound<MessageResponse>("User not found.");
        }

        if (!user.IsDeleted)
        {
            return ServiceResult.Failure<MessageResponse>("User account is currently active.");
        }

        user.IsDeleted = false;
        user.UpdatedAt = DateTimeOffset.UtcNow;

        // Verify IdentityResult — do not return success if DB update fails
        var updateResult = await _userManager.UpdateAsync(user);
        if (!updateResult.Succeeded)
        {
            return ServiceResult.InfrastructureError<MessageResponse>(
                string.Join("; ", updateResult.Errors.Select(e => e.Description)));
        }

        return ServiceResult.Success(
            new MessageResponse("User account has been re-enabled successfully."));
    }

    private async Task<AuthResponse> GenerateAuthTokensAsync(AppUser user, string? role,
        CancellationToken cancellationToken)
    {
        var userRoles = await _userManager.GetRolesAsync(user);

        var primaryRole = !string.IsNullOrEmpty(role) && userRoles.Contains(role)
            ? role
            : (userRoles.Contains("Admin")
                ? "Admin"
                : userRoles.Contains("Employer")
                    ? "Employer"
                    : userRoles.FirstOrDefault() ?? string.Empty);

        var jwtInfo = new JwtUserInfo(
            UserId: user.Id,
            Email: user.Email!,
            Roles: userRoles.AsReadOnly(),
            SecurityStamp: user.SecurityStamp);

        var accessToken = _jwtTokenService.GenerateAccessToken(jwtInfo);

        var expiryMinutes = int.TryParse(
            _configuration["Jwt:AccessTokenExpiryMinutes"], out var m)
            ? m
            : 15;
        var accessTokenExpiresAt = DateTimeOffset.UtcNow.AddMinutes(expiryMinutes);

        var rawRefreshToken = _jwtTokenService.GenerateRefreshToken();
        var tokenHash = _jwtTokenService.HashRefreshToken(rawRefreshToken);
        var expiryDays = int.TryParse(
            _configuration["Jwt:RefreshTokenExpiryDays"], out var d)
            ? d
            : 7;

        var refreshToken = new RefreshToken
        {
            Id = Guid.NewGuid(),
            UserId = user.Id,
            TokenHash = tokenHash,
            ExpiresAt = DateTimeOffset.UtcNow.AddDays(expiryDays),
            CreatedAt = DateTimeOffset.UtcNow
        };
        _context.RefreshTokens.Add(refreshToken);

        user.LastLoginAt = DateTimeOffset.UtcNow;
        user.UpdatedAt = DateTimeOffset.UtcNow;
        await _userManager.UpdateAsync(user);

        // Set HttpOnly cookie for refresh token
        _tokenCookieService.SetRefreshToken(rawRefreshToken);

        return new AuthResponse(
            AccessToken: accessToken,
            AccessTokenExpiresAt: accessTokenExpiresAt,
            RefreshToken: rawRefreshToken,
            Role: primaryRole,
            Roles: userRoles.ToList().AsReadOnly());
    }


    public async Task<ServiceResult<AuthResponse>> GoogleLoginAsync(
        GoogleLoginRequest request,
        CancellationToken cancellationToken = default)
    {
        var validationResult = await _googleLoginValidator.ValidateAsync(request, cancellationToken);
        if (!validationResult.IsValid)
            return ServiceResult.Failure<AuthResponse>(string.Join(" ",
                validationResult.Errors.Select(e => e.ErrorMessage)));

        var payload = await _googleTokenValidator.ValidateAsync(request.GoogleIdToken);
        if (payload == null)
            return ServiceResult.Unauthorized<AuthResponse>("Invalid Google ID token.");

        var existingUser = await _userManager.FindByEmailAsync(payload.Email);
        if (existingUser == null)
            return ServiceResult.NotFound<AuthResponse>("User not found. Please register.");

        if (existingUser.IsDeleted)
            return ServiceResult.Forbidden<AuthResponse>("Tài khoản đã bị vô hiệu hóa.");

        var logins = await _userManager.GetLoginsAsync(existingUser);
        if (!logins.Any(l => l.LoginProvider == "Google"))
            return
                ServiceResult.Conflict<AuthResponse>(
                    "REQUIRE_PASSWORD_LOGIN_TO_LINK"); // Account exists with password, needs linking

        var authResponse = await GenerateAuthTokensAsync(existingUser, role: null, cancellationToken);
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(authResponse);
    }

    public async Task<ServiceResult<AuthResponse>> GoogleRegisterCandidateAsync(
        GoogleLoginRequest request,
        CancellationToken cancellationToken = default)
    {
        var validationResult = await _googleLoginValidator.ValidateAsync(request, cancellationToken);
        if (!validationResult.IsValid)
            return ServiceResult.Failure<AuthResponse>(string.Join(" ",
                validationResult.Errors.Select(e => e.ErrorMessage)));

        var payload = await _googleTokenValidator.ValidateAsync(request.GoogleIdToken);
        if (payload == null)
            return ServiceResult.Unauthorized<AuthResponse>("Invalid Google ID token.");

        var targetRole = "Candidate";

        using var transaction = await _context.Database.BeginTransactionAsync(cancellationToken);
        try
        {
            var existingUser = await _userManager.FindByEmailAsync(payload.Email);
            if (existingUser != null)
            {
                if (existingUser.IsDeleted)
                    return ServiceResult.Forbidden<AuthResponse>("Tài khoản đã bị vô hiệu hóa.");

                var logins = await _userManager.GetLoginsAsync(existingUser);
                if (!logins.Any(l => l.LoginProvider == "Google"))
                    return ServiceResult.Conflict<AuthResponse>("REQUIRE_PASSWORD_LOGIN_TO_LINK");

                if (await _userManager.IsInRoleAsync(existingUser, targetRole))
                    return ServiceResult.Conflict<AuthResponse>("ACCOUNT_ALREADY_EXISTS");

                // Add Candidate role & profile to existing user
                await _userManager.AddToRoleAsync(existingUser, targetRole);
                var newCandidate = new Candidate
                {
                    UserId = existingUser.Id,
                    FullName = payload.Name ?? payload.Email
                };
                _context.Candidates.Add(newCandidate);
                var existingAuthResponse = await GenerateAuthTokensAsync(existingUser, targetRole, cancellationToken);
                await _context.SaveChangesAsync(cancellationToken);
                await transaction.CommitAsync(cancellationToken);
                return ServiceResult.Success(existingAuthResponse);
            }

            var user = new AppUser
            {
                Id = Guid.NewGuid(),
                UserName = payload.Email,
                Email = payload.Email,
                EmailConfirmed = payload.EmailVerified,
                CreatedAt = DateTimeOffset.UtcNow,
                UpdatedAt = DateTimeOffset.UtcNow,
                IsDeleted = false
            };

            var createResult = await _userManager.CreateAsync(user); // No password
            if (!createResult.Succeeded)
                return ServiceResult.Failure<AuthResponse>(string.Join(" ",
                    createResult.Errors.Select(e => e.Description)));

            var loginInfo = new UserLoginInfo("Google", payload.Subject, "Google");
            await _userManager.AddLoginAsync(user, loginInfo);
            await _userManager.AddToRoleAsync(user, targetRole);

            var candidate = new Candidate
            {
                UserId = user.Id,
                FullName = payload.Name ?? payload.Email
            };
            _context.Candidates.Add(candidate);

            var authResponse = await GenerateAuthTokensAsync(user, targetRole, cancellationToken);
            await _context.SaveChangesAsync(cancellationToken);
            await transaction.CommitAsync(cancellationToken);

            return ServiceResult.Success(authResponse);
        }
        catch (DbUpdateException) // Catch unique constraint violations
        {
            await transaction.RollbackAsync(cancellationToken);
            return ServiceResult.Conflict<AuthResponse>("ACCOUNT_ALREADY_EXISTS");
        }
        catch (Exception)
        {
            await transaction.RollbackAsync(cancellationToken);
            return ServiceResult.InfrastructureError<AuthResponse>(
                "Registration failed due to a system error. Please try again.");
        }
    }

    public async Task<ServiceResult<AuthResponse>> GoogleRegisterEmployerAsync(
        GoogleRegisterEmployerRequest request,
        CancellationToken cancellationToken = default)
    {
        var validationResult = await _googleRegisterEmployerValidator.ValidateAsync(request, cancellationToken);
        if (!validationResult.IsValid)
            return ServiceResult.Failure<AuthResponse>(string.Join(" ",
                validationResult.Errors.Select(e => e.ErrorMessage)));

        var payload = await _googleTokenValidator.ValidateAsync(request.GoogleIdToken);
        if (payload == null)
            return ServiceResult.Unauthorized<AuthResponse>("Invalid Google ID token.");

        var targetRole = "Employer";

        using var transaction = await _context.Database.BeginTransactionAsync(cancellationToken);
        try
        {
            var existingUser = await _userManager.FindByEmailAsync(payload.Email);
            if (existingUser != null)
            {
                if (existingUser.IsDeleted)
                    return ServiceResult.Forbidden<AuthResponse>("Tài khoản đã bị vô hiệu hóa.");

                var logins = await _userManager.GetLoginsAsync(existingUser);
                if (!logins.Any(l => l.LoginProvider == "Google"))
                    return ServiceResult.Conflict<AuthResponse>("REQUIRE_PASSWORD_LOGIN_TO_LINK");

                if (await _userManager.IsInRoleAsync(existingUser, targetRole))
                    return ServiceResult.Conflict<AuthResponse>("ACCOUNT_ALREADY_EXISTS");

                // Multi-role logic: add Employer role to existing user
                await _userManager.AddToRoleAsync(existingUser, targetRole);
                var company = new Company
                {
                    Name = request.CompanyName,
                    TaxCode = "TEMP_" + Guid.NewGuid().ToString("N")[..8],
                    VerifiedStatus = CompanyVerificationStatus.Pending
                };
                _context.Companies.Add(company);
                await _context.SaveChangesAsync(cancellationToken);

                var employer = new Employer
                {
                    UserId = existingUser.Id,
                    FullName = payload.Name ?? payload.Email,
                    Phone = request.Phone,
                    CompanyId = company.Id
                };
                _context.Employers.Add(employer);

                var existingAuthResponse = await GenerateAuthTokensAsync(existingUser, targetRole, cancellationToken);
                await _context.SaveChangesAsync(cancellationToken);
                await transaction.CommitAsync(cancellationToken);
                return ServiceResult.Success(existingAuthResponse);
            }

            var user = new AppUser
            {
                Id = Guid.NewGuid(),
                UserName = payload.Email,
                Email = payload.Email,
                EmailConfirmed = payload.EmailVerified,
                CreatedAt = DateTimeOffset.UtcNow,
                UpdatedAt = DateTimeOffset.UtcNow,
                IsDeleted = false
            };

            var createResult = await _userManager.CreateAsync(user);
            if (!createResult.Succeeded)
                return ServiceResult.Failure<AuthResponse>(string.Join(" ",
                    createResult.Errors.Select(e => e.Description)));

            var loginInfo = new UserLoginInfo("Google", payload.Subject, "Google");
            await _userManager.AddLoginAsync(user, loginInfo);
            await _userManager.AddToRoleAsync(user, targetRole);

            var newCompany = new Company
            {
                Name = request.CompanyName,
                TaxCode = "TEMP_" + Guid.NewGuid().ToString("N")[..8],
                VerifiedStatus = CompanyVerificationStatus.Pending
            };
            _context.Companies.Add(newCompany);
            await _context.SaveChangesAsync(cancellationToken);

            var newEmployer = new Employer
            {
                UserId = user.Id,
                FullName = payload.Name ?? payload.Email,
                Phone = request.Phone,
                CompanyId = newCompany.Id
            };
            _context.Employers.Add(newEmployer);

            var authResponse = await GenerateAuthTokensAsync(user, targetRole, cancellationToken);
            await _context.SaveChangesAsync(cancellationToken);
            await transaction.CommitAsync(cancellationToken);

            return ServiceResult.Success(authResponse);
        }
        catch (DbUpdateException)
        {
            await transaction.RollbackAsync(cancellationToken);
            return ServiceResult.Conflict<AuthResponse>("ACCOUNT_ALREADY_EXISTS");
        }
        catch (Exception)
        {
            await transaction.RollbackAsync(cancellationToken);
            return ServiceResult.InfrastructureError<AuthResponse>(
                "Registration failed due to a system error. Please try again.");
        }
    }
}
