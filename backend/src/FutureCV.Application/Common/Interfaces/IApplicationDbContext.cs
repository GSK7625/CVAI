using System;
using System.Threading;
using System.Threading.Tasks;
using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace FutureCV.Application.Common.Interfaces;

/// <summary>
/// Contract for the EF Core DbContext exposed to the Application layer.
/// The Application layer never depends on Infrastructure directly.
/// </summary>
public interface IApplicationDbContext
{
    DbSet<RefreshToken> RefreshTokens { get; }
    DbSet<Company> Companies { get; }
    DbSet<Employer> Employers { get; }
    DbSet<Candidate> Candidates { get; }
    DbSet<Education> Educations { get; }
    DbSet<Experience> Experiences { get; }
    DbSet<Skill> Skills { get; }
    DbSet<CandidateSkill> CandidateSkills { get; }
    DbSet<CandidateCv> CandidateCvs { get; }
    DbSet<CvParser> CvParsers { get; }
    DbSet<CvEvaluation> CvEvaluations { get; }
    DbSet<Certificate> Certificates { get; }
    DbSet<Project> Projects { get; }
    DbSet<AuditLog> AuditLogs { get; }

    DbSet<Location> Locations { get; }
    DbSet<JobCategory> JobCategories { get; }
    DbSet<JobLevel> JobLevels { get; }
    DbSet<EmploymentType> EmploymentTypes { get; }
    DbSet<Job> Jobs { get; }
    DbSet<JobSkill> JobSkills { get; }
    DbSet<SavedJob> SavedJobs { get; }
    DbSet<JobApplication> Applications { get; }
    DbSet<ApplicationStatusHistory> ApplicationStatusHistories { get; }
    DbSet<JobReport> JobReports { get; }


    Microsoft.EntityFrameworkCore.Infrastructure.DatabaseFacade Database { get; }
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
