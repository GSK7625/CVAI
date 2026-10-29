using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace FutureCV.Infrastructure.Persistence.Seeders;

/// <summary>
/// Unified entry point for database seeding on application startup.
/// Coordinates seeding of Identity (Roles, SuperAdmin) and Master Reference Data.
/// </summary>
public static class DatabaseSeeder
{
    public static async Task SeedAsync(IServiceProvider serviceProvider)
    {
        using var scope = serviceProvider.CreateScope();
        var logger = scope.ServiceProvider.GetService<ILoggerFactory>()?.CreateLogger(nameof(DatabaseSeeder));

        try
        {
            logger?.LogInformation("Starting database seeding pipeline...");

            // 1. Seed Roles & SuperAdmin user
            await RoleSeeder.SeedAsync(serviceProvider);

            // 2. Seed Master Reference Data (Categories, Levels, EmploymentTypes, Locations, Skills)
            await ReferenceDataSeeder.SeedAsync(serviceProvider);

            // 3. Seed Realistic Demo Presentation Data (Companies, Recruiter, Candidates, Jobs, CV, Application, MatchResult)
            await DemoDataSeeder.SeedAsync(serviceProvider);

            logger?.LogInformation("Database seeding pipeline completed successfully.");
        }
        catch (Exception ex)
        {
            logger?.LogError(ex, "An error occurred during database seeding.");
            throw;
        }
    }
}
