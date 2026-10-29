using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Features.AiMatching.Configurations;
using FutureCV.Application.Features.Auth.Interfaces;
using FutureCV.Infrastructure.Configurations;
using FutureCV.Infrastructure.Identity;
using FutureCV.Infrastructure.Persistence;
using FutureCV.Infrastructure.Services;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace FutureCV.Infrastructure;

/// <summary>
/// Extension method to register all Infrastructure services.
/// Called from the Api composition root (Program.cs).
/// </summary>
public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        var connectionString = configuration.GetConnectionString("DefaultConnection")
            ?? throw new InvalidOperationException("Connection string 'DefaultConnection' not found.");

        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseNpgsql(connectionString));

        // Register DbContext as IApplicationDbContext for Application layer
        services.AddScoped<IApplicationDbContext>(
            provider => provider.GetRequiredService<ApplicationDbContext>());

        // ASP.NET Core Identity — password rules, lockout, roles, EF stores, token providers
        services.AddIdentityCore<AppUser>(options =>
            {
                options.Password.RequireDigit = true;
                options.Password.RequiredLength = 6;
                options.Password.RequireUppercase = true;
                options.Password.RequireLowercase = true;
                options.Password.RequireNonAlphanumeric = false;

                options.Lockout.MaxFailedAccessAttempts = 5;
                options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(30);
                options.Lockout.AllowedForNewUsers = true;
            })
            .AddRoles<IdentityRole<Guid>>()
            .AddEntityFrameworkStores<ApplicationDbContext>()
            .AddDefaultTokenProviders();


        // Register JWT Token Service
        services.AddScoped<IJwtTokenService, JwtTokenService>();

        // Register Token Cookie Service
        services.AddScoped<ITokenCookieService, TokenCookieService>();

        // Register SmtpSettings & Email Service
        services.Configure<SmtpSettings>(configuration.GetSection("SmtpSettings"));
        services.AddTransient<IEmailService, EmailService>();

        // Register Auth Service
        services.AddScoped<IAuthService, AuthService>();

        // Register Google Token Validator
        services.AddScoped<IGoogleTokenValidator, GoogleTokenValidator>();

        // Register Identity service abstraction for Application layer
        services.AddScoped<IIdentityService, IdentityService>();

        // Register Cloudinary settings & file storage
        services.Configure<CloudinarySettings>(configuration.GetSection("Cloudinary"));
        services.AddScoped<CloudinaryFileStorage>();
        services.AddScoped<IFileStorage>(sp => sp.GetRequiredService<CloudinaryFileStorage>());

        // Register AI Service & AI Matching feature settings
        services.Configure<AiServiceOptions>(configuration.GetSection(AiServiceOptions.SectionName));
        services.Configure<AiMatchingFeatureOptions>(configuration.GetSection(AiMatchingFeatureOptions.SectionName));

        // Register AI Matching HTTP Client
        services.AddHttpClient<IAiMatchingClient, AiMatchingHttpClient>((serviceProvider, client) =>
        {
            var options = serviceProvider.GetService<Microsoft.Extensions.Options.IOptions<AiServiceOptions>>()?.Value ?? new AiServiceOptions();
            var config = serviceProvider.GetRequiredService<IConfiguration>();

            var baseUrl = !string.IsNullOrWhiteSpace(options.BaseUrl)
                ? options.BaseUrl
                : (config["AiService:BaseUrl"] ?? "http://localhost:8000");

            client.BaseAddress = new Uri(baseUrl.TrimEnd('/') + "/");

            var timeoutSec = options.TimeoutSeconds > 0
                ? options.TimeoutSeconds
                : (double.TryParse(config["AiService:TimeoutSeconds"], out var t) && t > 0 ? t : 90.0);

            client.Timeout = TimeSpan.FromSeconds(timeoutSec);
        });

        // Register AI CV HTTP Client for PDF analysis and extraction
        services.AddHttpClient<IAiCvClient, AiCvHttpClient>((serviceProvider, client) =>
        {
            var options = serviceProvider.GetService<Microsoft.Extensions.Options.IOptions<AiServiceOptions>>()?.Value ?? new AiServiceOptions();
            var config = serviceProvider.GetRequiredService<IConfiguration>();

            var baseUrl = !string.IsNullOrWhiteSpace(options.BaseUrl)
                ? options.BaseUrl
                : (config["AiService:BaseUrl"] ?? "http://localhost:8000");

            client.BaseAddress = new Uri(baseUrl.TrimEnd('/') + "/");

            var timeoutSec = options.TimeoutSeconds > 0
                ? options.TimeoutSeconds
                : (double.TryParse(config["AiService:TimeoutSeconds"], out var t) && t > 0 ? t : 90.0);

            client.Timeout = TimeSpan.FromSeconds(timeoutSec);
        });

        return services;
    }
}


