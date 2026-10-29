using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Admin.DTOs;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;

namespace FutureCV.Infrastructure.Identity;

/// <summary>
/// Infrastructure implementation of <see cref="IIdentityService"/> using ASP.NET Core Identity's <see cref="UserManager{TUser}"/>.
/// </summary>
public class IdentityService : IIdentityService
{
    private readonly UserManager<AppUser> _userManager;

    public IdentityService(UserManager<AppUser> userManager)
    {
        _userManager = userManager;
    }

    public async Task<string?> GetUserEmailAsync(Guid userId, CancellationToken cancellationToken = default)
    {
        var user = await _userManager.FindByIdAsync(userId.ToString());
        return user?.Email;
    }

    public async Task<PagedResult<IdentityUserInfo>> GetUsersAsync(
        UserQueryFilter filter, CancellationToken cancellationToken = default)
    {
        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize  = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var query = _userManager.Users.AsNoTracking();

        // 1. Search filter (Email or Phone)
        if (!string.IsNullOrWhiteSpace(filter.Search))
        {
            var search = filter.Search.Trim().ToLower();
            query = query.Where(u =>
                (u.Email != null && u.Email.ToLower().Contains(search)) ||
                (u.PhoneNumber != null && u.PhoneNumber.Contains(search)));
        }

        // 2. Lock status filter
        if (filter.IsLocked.HasValue)
        {
            var now = DateTimeOffset.UtcNow;
            query = filter.IsLocked.Value
                ? query.Where(u => u.LockoutEnd != null && u.LockoutEnd > now)
                : query.Where(u => u.LockoutEnd == null || u.LockoutEnd <= now);
        }

        // 3. Role filter
        if (!string.IsNullOrWhiteSpace(filter.Role))
        {
            var roleName = filter.Role.Trim();
            var usersInRole = await _userManager.GetUsersInRoleAsync(roleName);
            var userIdsInRole = usersInRole.Select(u => u.Id).ToList();

            query = query.Where(u => userIdsInRole.Contains(u.Id));
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var users = await query
            .OrderByDescending(u => u.CreatedAt)
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        var items = new List<IdentityUserInfo>();
        var nowCheck = DateTimeOffset.UtcNow;

        foreach (var u in users)
        {
            var roles = await _userManager.GetRolesAsync(u);
            var isLocked = u.LockoutEnd.HasValue && u.LockoutEnd.Value > nowCheck;

            items.Add(new IdentityUserInfo(
                u.Id,
                u.Email ?? string.Empty,
                u.PhoneNumber,
                roles.ToList(),
                isLocked,
                u.LockoutEnd,
                u.CreatedAt
            ));
        }

        return new PagedResult<IdentityUserInfo>(items, totalCount, pageIndex, pageSize);
    }

    public async Task<ServiceResult<bool>> LockUserAsync(
        Guid targetUserId, CancellationToken cancellationToken = default)
    {
        var targetUser = await _userManager.FindByIdAsync(targetUserId.ToString());
        if (targetUser is null)
            return ServiceResult.NotFound<bool>("Target user not found.");

        var lockResult = await _userManager.SetLockoutEndDateAsync(targetUser, DateTimeOffset.MaxValue);
        if (!lockResult.Succeeded)
        {
            var errorMsg = string.Join("; ", lockResult.Errors.Select(e => e.Description));
            return ServiceResult.Failure<bool>($"Failed to lock user: {errorMsg}");
        }

        return ServiceResult.Success(true);
    }

    public async Task<ServiceResult<bool>> UnlockUserAsync(
        Guid targetUserId, CancellationToken cancellationToken = default)
    {
        var targetUser = await _userManager.FindByIdAsync(targetUserId.ToString());
        if (targetUser is null)
            return ServiceResult.NotFound<bool>("Target user not found.");

        var unlockResult = await _userManager.SetLockoutEndDateAsync(targetUser, null);
        if (!unlockResult.Succeeded)
        {
            var errorMsg = string.Join("; ", unlockResult.Errors.Select(e => e.Description));
            return ServiceResult.Failure<bool>($"Failed to unlock user: {errorMsg}");
        }

        await _userManager.ResetAccessFailedCountAsync(targetUser);
        return ServiceResult.Success(true);
    }

    public async Task<AdminUserStatsDto> GetUserStatsAsync(CancellationToken cancellationToken = default)
    {
        var now = DateTimeOffset.UtcNow;
        var thirtyDaysAgo = now.AddDays(-30);

        var totalUsers = await _userManager.Users.CountAsync(cancellationToken);
        var lockedUsersCount = await _userManager.Users
            .CountAsync(u => u.LockoutEnd != null && u.LockoutEnd > now, cancellationToken);
        var newUsersLast30Days = await _userManager.Users
            .CountAsync(u => u.CreatedAt >= thirtyDaysAgo, cancellationToken);

        var candidateUsers = await _userManager.GetUsersInRoleAsync("Candidate");
        var employerUsers = await _userManager.GetUsersInRoleAsync("Employer");

        return new AdminUserStatsDto(
            totalUsers,
            candidateUsers.Count,
            employerUsers.Count,
            lockedUsersCount,
            newUsersLast30Days);
    }
}
