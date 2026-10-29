using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Auth.DTOs;

namespace FutureCV.Application.Features.Auth.Interfaces;

/// <summary>
/// Service interface defining authentication and authorization operations.
/// </summary>
public interface IAuthService
{
    Task<ServiceResult<AuthResponse>> RegisterCandidateAsync(RegisterCandidateRequest request, CancellationToken cancellationToken = default);
    Task<ServiceResult<AuthResponse>> RegisterEmployerAsync(RegisterEmployerRequest request, CancellationToken cancellationToken = default);
    Task<ServiceResult<AuthResponse>> LoginAsync(LoginRequest request, CancellationToken cancellationToken = default);
    Task<ServiceResult<AuthResponse>> GoogleLoginAsync(GoogleLoginRequest request, CancellationToken cancellationToken = default);
    Task<ServiceResult<AuthResponse>> GoogleRegisterCandidateAsync(GoogleLoginRequest request, CancellationToken cancellationToken = default);
    Task<ServiceResult<AuthResponse>> GoogleRegisterEmployerAsync(GoogleRegisterEmployerRequest request, CancellationToken cancellationToken = default);
    Task<ServiceResult<AuthResponse>> RefreshTokenAsync(RefreshTokenRequest request, CancellationToken cancellationToken = default);
    Task<ServiceResult<MessageResponse>> LogoutAsync(Guid userId, string? refreshToken = null, CancellationToken cancellationToken = default);
    Task<ServiceResult<MessageResponse>> LogoutAllAsync(Guid userId, CancellationToken cancellationToken = default);
    Task<ServiceResult<MessageResponse>> ForgotPasswordAsync(ForgotPasswordRequest request, CancellationToken cancellationToken = default);
    Task<ServiceResult<MessageResponse>> ResetPasswordAsync(ResetPasswordRequest request, CancellationToken cancellationToken = default);
    Task<ServiceResult<MessageResponse>> DisableUserAsync(Guid targetUserId, Guid currentAdminId, CancellationToken cancellationToken = default);
    Task<ServiceResult<MessageResponse>> EnableUserAsync(Guid userId, CancellationToken cancellationToken = default);
}
