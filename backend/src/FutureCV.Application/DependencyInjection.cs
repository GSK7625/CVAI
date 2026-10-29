using FluentValidation;
using FutureCV.Application.Features.Admin.Interfaces;
using FutureCV.Application.Features.Admin.Services;
using FutureCV.Application.Features.Candidate.Interfaces;
using FutureCV.Application.Features.Candidate.Services;
using FutureCV.Application.Features.Employer.Interfaces;
using FutureCV.Application.Features.Employer.Services;
using FutureCV.Application.Features.Job.Interfaces;
using FutureCV.Application.Features.Job.Services;
using FutureCV.Application.Features.JobApplication.Interfaces;
using FutureCV.Application.Features.JobApplication.Services;
using Microsoft.Extensions.DependencyInjection;

namespace FutureCV.Application;

/// <summary>
/// Extension method to register all Application-layer services.
/// Automatically registers all FluentValidation validators in this assembly and business services.
/// </summary>
public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddValidatorsFromAssembly(typeof(DependencyInjection).Assembly);

        // Business use case services
        services.AddScoped<ICandidateService, CandidateService>();
        services.AddScoped<IEmployerService, EmployerService>();
        services.AddScoped<IJobService, JobService>();
        services.AddScoped<IApplicationService, ApplicationService>();
        services.AddScoped<IAdminService, AdminService>();

        return services;
    }
}
