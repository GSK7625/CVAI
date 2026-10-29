using System.Security.Claims;
using FutureCV.Infrastructure.Identity;
using Microsoft.AspNetCore.Identity;

namespace FutureCV.Api.Middlewares;

/// <summary>
/// Middleware to verify if an authenticated user's account has been disabled (IsDeleted = true).
/// If disabled, immediately aborts the pipeline and returns 403 Forbidden (BR-07).
/// </summary>
public class BannedUserMiddleware
{
    private readonly RequestDelegate _next;

    public BannedUserMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context, IServiceProvider serviceProvider)
    {
        if (context.User.Identity?.IsAuthenticated == true)
        {
            var userIdStr = context.User.FindFirstValue(ClaimTypes.NameIdentifier);
            if (Guid.TryParse(userIdStr, out var userId))
            {
                using var scope = serviceProvider.CreateScope();
                var userManager = scope.ServiceProvider.GetRequiredService<UserManager<AppUser>>();
                var user = await userManager.FindByIdAsync(userId.ToString());

                if (user is null || user.IsDeleted)
                {
                    context.Response.StatusCode = StatusCodes.Status403Forbidden;
                    context.Response.ContentType = "application/json";
                    await context.Response.WriteAsJsonAsync(new { message = "Account has been disabled. Please contact support." });
                    return;
                }
            }
        }

        await _next(context);
    }
}
