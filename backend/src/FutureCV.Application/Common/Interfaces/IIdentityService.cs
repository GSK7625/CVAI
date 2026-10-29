using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Admin.DTOs;

namespace FutureCV.Application.Common.Interfaces;

/// <summary>
/// Abstraction for identity querying and management operations required by the Application layer.
/// Prevents Application layer services from directly coupling to ASP.NET Core Identity's UserManager.
/// </summary>
public interface IIdentityService
{
    Task<string?> GetUserEmailAsync(Guid userId, CancellationToken cancellationToken = default);

    Task<PagedResult<IdentityUserInfo>> GetUsersAsync(UserQueryFilter filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> LockUserAsync(Guid targetUserId, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> UnlockUserAsync(Guid targetUserId, CancellationToken cancellationToken = default);

    Task<AdminUserStatsDto> GetUserStatsAsync(CancellationToken cancellationToken = default);
}
