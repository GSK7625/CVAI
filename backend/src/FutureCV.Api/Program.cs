using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using FutureCV.Api.Middlewares;
using FutureCV.Application;
using FutureCV.Infrastructure;
using FutureCV.Infrastructure.Identity;
using FutureCV.Infrastructure.Persistence.Seeders;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Identity;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using SharpGrip.FluentValidation.AutoValidation.Mvc.Extensions;

var builder = WebApplication.CreateBuilder(args);

// ── Services ──────────────────────────────────────────────────
builder.Services.AddControllers();
builder.Services.AddHttpContextAccessor();

// Global Exception Handling & RFC 7807 ProblemDetails
builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
builder.Services.AddProblemDetails();

// Application layer (use-case services, validators registered via AddValidatorsFromAssembly)
builder.Services.AddApplication();

// Enable automatic asynchronous FluentValidation for API controllers
builder.Services.AddFluentValidationAutoValidation();

// Infrastructure layer (DbContext, Identity, JWT, Auth services)
builder.Services.AddInfrastructure(builder.Configuration);

// Password reset token lifetime: 15 min (overrides Identity default of 1 day)
// Configured here (Api project) because DataProtectionTokenProviderOptions requires
// the full ASP.NET Core SDK — not available in Infrastructure class library.
builder.Services.Configure<DataProtectionTokenProviderOptions>(options =>
    options.TokenLifespan = TimeSpan.FromMinutes(15));

// JWT Authentication
var jwtKey = builder.Configuration["Jwt:Key"]
    ?? throw new InvalidOperationException("JWT Key is not configured in appsettings.");
var jwtIssuer = builder.Configuration["Jwt:Issuer"];
var jwtAudience = builder.Configuration["Jwt:Audience"];

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = jwtIssuer,
        ValidAudience = jwtAudience,
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
        ClockSkew = TimeSpan.Zero
    };
    options.Events = new JwtBearerEvents
    {
        OnTokenValidated = async context =>
        {
            var userId = context.Principal?.FindFirst(ClaimTypes.NameIdentifier)?.Value
                ?? context.Principal?.FindFirst(JwtRegisteredClaimNames.Sub)?.Value;
            var stamp = context.Principal?.FindFirst("stamp")?.Value;
            if (string.IsNullOrEmpty(userId))
            {
                context.Fail("Missing user identifier.");
                return;
            }

            var userManager = context.HttpContext.RequestServices
                .GetRequiredService<UserManager<AppUser>>();
            var user = await userManager.FindByIdAsync(userId);
            if (user is null || user.IsDeleted ||
                (!string.IsNullOrEmpty(user.SecurityStamp) &&
                 !string.Equals(user.SecurityStamp, stamp, StringComparison.Ordinal)))
            {
                context.Fail("Session has been invalidated.");
            }
        }
    };
});

// Swagger / OpenAPI with Bearer support
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo { Title = "FutureCV API", Version = "v1" });
    options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = SecuritySchemeType.Http,
        Scheme = "Bearer",
        BearerFormat = "JWT",
        In = ParameterLocation.Header,
        Description = "Enter JWT Bearer token"
    });
    options.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            Array.Empty<string>()
        }
    });
});

// CORS — restrict to configured frontend origins in non-development environments
var configuredOrigins = builder.Configuration
    .GetSection("Cors:AllowedOrigins")
    .Get<string[]>()?
    .Where(o => !string.IsNullOrWhiteSpace(o))
    .Select(o => o.Trim().TrimEnd('/'))
    .Distinct(StringComparer.OrdinalIgnoreCase)
    .ToArray() ?? [];

var frontendOrigin = builder.Configuration["FrontendUrl"]?.Trim().TrimEnd('/');
var allowedOrigins = !string.IsNullOrWhiteSpace(frontendOrigin) &&
    !configuredOrigins.Contains(frontendOrigin, StringComparer.OrdinalIgnoreCase)
    ? [.. configuredOrigins, frontendOrigin]
    : configuredOrigins;

if (!builder.Environment.IsDevelopment() && allowedOrigins.Length == 0)
{
    throw new InvalidOperationException(
        "Cors:AllowedOrigins or FrontendUrl must be configured in non-development environments.");
}

builder.Services.AddCors(options =>
{
    options.AddPolicy("FrontendCors", policy =>
    {
        if (builder.Environment.IsDevelopment())
        {
            policy.SetIsOriginAllowed(origin =>
                    allowedOrigins.Contains(origin.TrimEnd('/'), StringComparer.OrdinalIgnoreCase) ||
                    (Uri.TryCreate(origin, UriKind.Absolute, out var uri) &&
                     (uri.Host.Equals("localhost", StringComparison.OrdinalIgnoreCase) ||
                      uri.Host.Equals("127.0.0.1", StringComparison.OrdinalIgnoreCase))))
                .AllowAnyHeader()
                .AllowAnyMethod()
                .AllowCredentials();
        }
        else
        {
            policy.WithOrigins(allowedOrigins)
                .AllowAnyHeader()
                .AllowAnyMethod()
                .AllowCredentials();
        }
    });
});

// ── Pipeline ──────────────────────────────────────────────────
var app = builder.Build();

app.UseExceptionHandler();

// Seed database on startup (Roles, SuperAdmin, Master Reference Data; DemoData in Development only)
await DatabaseSeeder.SeedAsync(app.Services, app.Environment.IsDevelopment());

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseCors("FrontendCors");
app.UseAuthentication();
app.UseAuthorization();
app.UseMiddleware<BannedUserMiddleware>();
app.MapControllers();

app.Run();

