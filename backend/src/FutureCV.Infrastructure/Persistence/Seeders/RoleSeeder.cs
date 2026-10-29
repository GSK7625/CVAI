using FutureCV.Infrastructure.Identity;
using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace FutureCV.Infrastructure.Persistence.Seeders;

/// <summary>
/// Seeds fixed system roles (Candidate, Employer, Admin) and the initial SuperAdmin account.
/// Idempotent: checks for existence before creating.
/// </summary>
public static class RoleSeeder
{
    private static readonly string[] Roles = { "Candidate", "Employer", "Admin" };

    public static async Task SeedAsync(IServiceProvider serviceProvider)
    {
        using var scope = serviceProvider.CreateScope();
        var roleManager = scope.ServiceProvider.GetRequiredService<RoleManager<IdentityRole<Guid>>>();
        var userManager = scope.ServiceProvider.GetRequiredService<UserManager<AppUser>>();
        var configuration = scope.ServiceProvider.GetService<IConfiguration>();
        var logger = scope.ServiceProvider.GetService<ILoggerFactory>()?.CreateLogger(nameof(RoleSeeder));

        // 1. Seed Roles
        foreach (var roleName in Roles)
        {
            if (!await roleManager.RoleExistsAsync(roleName))
            {
                var roleResult = await roleManager.CreateAsync(new IdentityRole<Guid>(roleName));
                if (roleResult.Succeeded)
                {
                    logger?.LogInformation("Seeded role: {RoleName}", roleName);
                }
            }
        }

        // 2. Seed Super Admin (Credentials loaded from configuration/env, with dev fallback)
        var adminEmail = configuration?["SuperAdmin:Email"] ?? "admin@futurecv.com";
        var adminPassword = configuration?["SuperAdmin:Password"] ?? "Admin@123456";

        var existingAdmin = await userManager.FindByEmailAsync(adminEmail);
        if (existingAdmin == null)
        {
            var adminUser = new AppUser
            {
                Id = Guid.NewGuid(),
                UserName = adminEmail,
                Email = adminEmail,
                CreatedAt = DateTimeOffset.UtcNow,
                UpdatedAt = DateTimeOffset.UtcNow
            };

            var createResult = await userManager.CreateAsync(adminUser, adminPassword);
            if (createResult.Succeeded)
            {
                await userManager.AddToRoleAsync(adminUser, "Admin");
                logger?.LogInformation("Seeded SuperAdmin account: {AdminEmail}", adminEmail);
            }
            else
            {
                logger?.LogWarning("Failed to seed SuperAdmin account: {Errors}",
                    string.Join(", ", createResult.Errors.Select(e => e.Description)));
            }
        }
    }
}
