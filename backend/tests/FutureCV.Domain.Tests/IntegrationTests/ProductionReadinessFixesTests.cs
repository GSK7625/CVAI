using System.Text;
using System.Text.Json;
using FluentValidation;
using FutureCV.Application;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.AiMatching.DTOs;
using FutureCV.Application.Features.Auth.DTOs;
using FutureCV.Application.Features.Auth.Interfaces;
using FutureCV.Application.Features.Candidate.Services;
using FutureCV.Application.Features.Job.DTOs;
using FutureCV.Application.Features.Job.Services;
using FutureCV.Application.Features.JobApplication.DTOs;
using FutureCV.Application.Features.JobApplication.Services;
using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;
using FutureCV.Infrastructure.Identity;
using FutureCV.Infrastructure.Persistence;
using FutureCV.Infrastructure.Persistence.Seeders;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace FutureCV.Domain.Tests.IntegrationTests;

public class ProductionReadinessFixesTests
{
    private sealed class StubFileStorage : IFileStorage
    {
        public int PreviewCalls { get; private set; }
        public string? LastPreviewPublicId { get; private set; }

        public string GetDocumentPreviewUrl(string publicId)
        {
            PreviewCalls++;
            LastPreviewPublicId = publicId;
            return $"https://api.cloudinary.com/v1_1/test/raw/download?public_id={Uri.EscapeDataString(publicId)}&expires_at=9999999999&signature=sig";
        }

        public Task<(string PublicUrl, string PublicId)> UploadAsync(
            Stream fileStream, string fileName, string folder, CancellationToken cancellationToken = default)
            => Task.FromResult(("https://res.cloudinary.com/test/image/upload/avatar.png", "avatars/test.png"));

        public Task<(string PublicUrl, string PublicId)> UploadDocumentAsync(
            Stream fileStream, string fileName, string folder, CancellationToken cancellationToken = default)
            => Task.FromResult(("https://res.cloudinary.com/test/raw/upload/cvs/candidates/builder.pdf", "cvs/candidates/builder.pdf"));

        public Task DeleteAsync(string publicId, CancellationToken cancellationToken = default) => Task.CompletedTask;
        public Task DeleteDocumentAsync(string publicId, CancellationToken cancellationToken = default) => Task.CompletedTask;
    }

    private sealed class StubIdentityService : IIdentityService
    {
        public Task<string?> GetUserEmailAsync(Guid userId, CancellationToken cancellationToken = default)
            => Task.FromResult<string?>("candidate@example.com");

        public Task<PagedResult<IdentityUserInfo>> GetUsersAsync(
            FutureCV.Application.Features.Admin.DTOs.UserQueryFilter filter, CancellationToken cancellationToken = default)
            => Task.FromResult(new PagedResult<IdentityUserInfo>([], 0, 1, 10));

        public Task<ServiceResult<bool>> LockUserAsync(Guid targetUserId, CancellationToken cancellationToken = default)
            => Task.FromResult(ServiceResult.Success(true));

        public Task<ServiceResult<bool>> UnlockUserAsync(Guid targetUserId, CancellationToken cancellationToken = default)
            => Task.FromResult(ServiceResult.Success(true));

        public Task<FutureCV.Application.Features.Admin.DTOs.AdminUserStatsDto> GetUserStatsAsync(CancellationToken cancellationToken = default)
            => Task.FromResult(new FutureCV.Application.Features.Admin.DTOs.AdminUserStatsDto(0, 0, 0, 0, 0));
    }

    private sealed class StubAiMatchingClient : IAiMatchingClient
    {
        public Task<ServiceResult<AiMatchResultDto>> MatchAsync(
            AiMatchRequest request, string? correlationId = null, CancellationToken cancellationToken = default)
            => throw new InvalidOperationException("Legacy AI matcher should not be invoked.");
    }

    private sealed class StubEvidenceClient : IEvidenceReviewClient
    {
        public bool Enabled => true;
        public int ExtractCalls { get; private set; }
        public int ReviewCalls { get; private set; }
        public string? LastReviewedCvText { get; private set; }

        public Task<ServiceResult<string>> ExtractPdfFromUrlAsync(string fileUrl, CancellationToken cancellationToken, string? publicId = null)
        {
            ExtractCalls++;
            return Task.FromResult(ServiceResult.Failure<string>("PDF has no text layer"));
        }

        public Task<ServiceResult<JsonElement>> ReviewAsync(string cvText, string jdText, string jobTitle, CancellationToken cancellationToken)
        {
            ReviewCalls++;
            LastReviewedCvText = cvText;
            return Task.FromResult(ServiceResult.Success(
                JsonSerializer.SerializeToElement(new { status = "ok", score = 80m, assessments = Array.Empty<object>() })));
        }
    }

    private static ApplicationDbContext CreateDbContext()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        return new ApplicationDbContext(options);
    }

    [Fact]
    public async Task BuilderUploadWithRawText_FeedsEvidenceReviewWithoutPdfOcr()
    {
        using var db = CreateDbContext();
        var userId = Guid.NewGuid();
        var candidateId = Guid.NewGuid();
        var jobId = Guid.NewGuid();

        db.Candidates.Add(new Candidate { Id = candidateId, UserId = userId, FullName = "Nguyen Van A" });
        db.Jobs.Add(new Job
        {
            Id = jobId,
            CompanyId = Guid.NewGuid(),
            PostedById = Guid.NewGuid(),
            Title = "Backend Engineer",
            Description = "Looking for .NET and PostgreSQL developer",
            IsActive = true,
            ApprovalStatus = JobApprovalStatus.Approved,
        });
        await db.SaveChangesAsync();

        var storage = new StubFileStorage();
        var evidence = new StubEvidenceClient();
        var candidateService = new CandidateService(
            db, storage, new StubIdentityService(), logger: NullLogger<CandidateService>.Instance, evidenceClient: evidence);

        await using var pdfStream = new MemoryStream(Encoding.ASCII.GetBytes("%PDF-1.4\n%image-only"));
        var upload = new FileUploadRequest(pdfStream, "NguyenVanA_CV.pdf", "application/pdf", pdfStream.Length);

        var uploadResult = await candidateService.UploadCvAsync(
            userId,
            upload,
            "CV từ Builder",
            rawText: "Nguyen Van A\nEXPERIENCE\nBackend Engineer - .NET & PostgreSQL",
            source: "Builder");

        Assert.True(uploadResult.IsSuccess);
        var savedCv = await db.CandidateCvs.Include(c => c.CvParser).FirstAsync(c => c.Id == uploadResult.Data!.Id);
        Assert.Equal("Builder", savedCv.Source);
        Assert.Equal("TextExtracted", savedCv.ParseStatus);
        Assert.NotNull(savedCv.CvParser);
        Assert.Contains("Backend Engineer", savedCv.CvParser!.RawText);

        var appService = new ApplicationService(
            db, new StubIdentityService(), new StubAiMatchingClient(), evidenceClient: evidence, fileStorage: storage);
        var preview = await appService.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(savedCv.Id));

        Assert.True(preview.IsSuccess);
        Assert.Equal("evidence", preview.Data!.MatchSource);
        Assert.Equal(0, evidence.ExtractCalls);
        Assert.Equal(1, evidence.ReviewCalls);
        Assert.Contains("Backend Engineer", evidence.LastReviewedCvText);
    }

    [Fact]
    public async Task ReapplyAfterWithdraw_ReactivatesSingleApplicationAndKeepsHistory()
    {
        using var db = CreateDbContext();
        var userId = Guid.NewGuid();
        var candidateId = Guid.NewGuid();
        var cvId = Guid.NewGuid();
        var jobId = Guid.NewGuid();

        db.Candidates.Add(new Candidate
        {
            Id = candidateId,
            UserId = userId,
            FullName = "Tran Thi B",
            CVs = [new CandidateCv { Id = cvId, CandidateId = candidateId, Title = "Main CV", Source = "Upload", ParseStatus = "Pending" }]
        });
        db.Jobs.Add(new Job
        {
            Id = jobId,
            CompanyId = Guid.NewGuid(),
            PostedById = Guid.NewGuid(),
            Title = "Frontend Engineer",
            Description = "React TypeScript",
            IsActive = true,
            ApprovalStatus = JobApprovalStatus.Approved,
        });
        await db.SaveChangesAsync();

        var service = new ApplicationService(db, new StubIdentityService(), new StubAiMatchingClient());

        var firstApply = await service.ApplyJobAsync(userId, jobId, new ApplyJobRequest(cvId, "First cover letter"));
        Assert.True(firstApply.IsSuccess);
        var appId = firstApply.Data!.ApplicationId;

        var duplicateApply = await service.ApplyJobAsync(userId, jobId, new ApplyJobRequest(cvId, "Duplicate"));
        Assert.False(duplicateApply.IsSuccess);
        Assert.Equal(ServiceErrorType.Conflict, duplicateApply.ErrorType);

        var withdraw = await service.WithdrawApplicationAsync(userId, appId, new WithdrawApplicationRequest("Updating CV"));
        Assert.True(withdraw.IsSuccess);

        var reapply = await service.ApplyJobAsync(userId, jobId, new ApplyJobRequest(cvId, "Updated cover letter"));
        Assert.True(reapply.IsSuccess);
        Assert.Equal(appId, reapply.Data!.ApplicationId);
        Assert.Equal("Applied", reapply.Data.Status);

        Assert.Equal(1, await db.Applications.CountAsync(a => a.CandidateId == candidateId && a.JobId == jobId));
        var histories = await db.ApplicationStatusHistories
            .Where(h => h.ApplicationId == appId)
            .OrderBy(h => h.ChangedAt)
            .ToListAsync();
        Assert.Equal(3, histories.Count);
        Assert.Equal((null, "Applied"), (histories[0].FromStatus, histories[0].ToStatus));
        Assert.Equal(("Applied", "Withdrawn"), (histories[1].FromStatus, histories[1].ToStatus));
        Assert.Equal(("Withdrawn", "Applied"), (histories[2].FromStatus, histories[2].ToStatus));
    }

    [Fact]
    public async Task RecruiterCvPreviewUrl_VerifiesCompanyOwnershipAndReturnsSignedUrl()
    {
        using var db = CreateDbContext();
        var companyA = Guid.NewGuid();
        var companyB = Guid.NewGuid();
        var recruiterAUserId = Guid.NewGuid();
        var recruiterBUserId = Guid.NewGuid();
        var candidateId = Guid.NewGuid();
        var cvId = Guid.NewGuid();
        var jobId = Guid.NewGuid();
        var appId = Guid.NewGuid();

        db.Employers.AddRange(
            new Employer { Id = Guid.NewGuid(), UserId = recruiterAUserId, CompanyId = companyA, FullName = "HR A" },
            new Employer { Id = Guid.NewGuid(), UserId = recruiterBUserId, CompanyId = companyB, FullName = "HR B" });
        db.Candidates.Add(new Candidate { Id = candidateId, UserId = Guid.NewGuid(), FullName = "Applicant" });
        db.CandidateCvs.Add(new CandidateCv
        {
            Id = cvId,
            CandidateId = candidateId,
            Title = "Applicant CV",
            FileUrl = "https://res.cloudinary.com/test/raw/upload/cvs/candidates/applicant.pdf",
            PublicId = "cvs/candidates/applicant.pdf",
            Source = "Upload",
            ParseStatus = "Pending",
        });
        db.Jobs.Add(new Job
        {
            Id = jobId,
            CompanyId = companyA,
            PostedById = recruiterAUserId,
            Title = "QA Engineer",
            Description = "Testing",
            IsActive = true,
            ApprovalStatus = JobApprovalStatus.Approved,
        });
        db.Applications.Add(new JobApplication
        {
            Id = appId,
            CandidateId = candidateId,
            JobId = jobId,
            CvId = cvId,
            Status = ApplicationStatus.Applied,
        });
        await db.SaveChangesAsync();

        var storage = new StubFileStorage();
        var service = new ApplicationService(
            db, new StubIdentityService(), new StubAiMatchingClient(), fileStorage: storage);

        var denied = await service.GetApplicationCvPreviewUrlAsync(recruiterBUserId, appId);
        Assert.False(denied.IsSuccess);
        Assert.Equal(ServiceErrorType.Forbidden, denied.ErrorType);
        Assert.Equal(0, storage.PreviewCalls);

        var allowed = await service.GetApplicationCvPreviewUrlAsync(recruiterAUserId, appId);
        Assert.True(allowed.IsSuccess);
        Assert.StartsWith("https://api.cloudinary.com/", allowed.Data);
        Assert.Contains("signature=", allowed.Data);
        Assert.Equal(1, storage.PreviewCalls);
        Assert.Equal("cvs/candidates/applicant.pdf", storage.LastPreviewPublicId);
    }

    [Fact]
    public async Task RoleSeeder_ThrowsInProduction_WhenSuperAdminCredentialsAreMissingOrPlaceholder()
    {
        var services = new ServiceCollection();
        var config = new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["SuperAdmin:Email"] = "admin@example.com",
                ["SuperAdmin:Password"] = "YOUR_SUPERADMIN_PASSWORD",
            })
            .Build();
        services.AddSingleton<IConfiguration>(config);
        services.AddLogging();
        services.AddDataProtection();
        services.AddDbContext<ApplicationDbContext>(o => o.UseInMemoryDatabase(Guid.NewGuid().ToString()));
        services.AddIdentityCore<AppUser>()
            .AddRoles<IdentityRole<Guid>>()
            .AddEntityFrameworkStores<ApplicationDbContext>();

        using var provider = services.BuildServiceProvider();

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => RoleSeeder.SeedAsync(provider, isDevelopment: false));
    }

    private sealed class StubEmailService : IEmailService
    {
        public Task SendEmailAsync(string toEmail, string subject, string bodyHtml, CancellationToken cancellationToken = default)
            => Task.CompletedTask;
    }

    private sealed class StubGoogleTokenValidator : IGoogleTokenValidator
    {
        public Task<GoogleTokenPayload?> ValidateAsync(string idToken) => Task.FromResult<GoogleTokenPayload?>(null);
    }

    private sealed class StubTokenCookieService : ITokenCookieService
    {
        public string? CookieValue { get; private set; }
        public int DeleteCount { get; private set; }
        public void SetRefreshToken(string refreshToken) => CookieValue = refreshToken;
        public void DeleteRefreshToken() { CookieValue = null; DeleteCount++; }
        public string? GetRefreshToken() => CookieValue;
    }

    private static (ServiceProvider Provider, StubTokenCookieService Cookies) BuildAuthTestProvider()
    {
        var services = new ServiceCollection();
        var config = new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Jwt:Key"] = "TEST_ONLY_JWT_SIGNING_KEY_AT_LEAST_32_CHARS!",
                ["Jwt:Issuer"] = "FutureCV.Test",
                ["Jwt:Audience"] = "FutureCV.Test",
                ["Jwt:AccessTokenExpiryMinutes"] = "15",
                ["Jwt:RefreshTokenExpiryDays"] = "7",
            })
            .Build();

        var dbName = Guid.NewGuid().ToString();
        services.AddSingleton<IConfiguration>(config);
        services.AddLogging();
        services.AddDataProtection();
        services.AddDbContext<ApplicationDbContext>(o => o
            .UseInMemoryDatabase(dbName)
            .ConfigureWarnings(w => w.Ignore(InMemoryEventId.TransactionIgnoredWarning)));
        services.AddScoped<IApplicationDbContext>(sp => sp.GetRequiredService<ApplicationDbContext>());

        services.AddIdentityCore<AppUser>(o =>
            {
                o.Password.RequireDigit = true;
                o.Password.RequiredLength = 6;
                o.Password.RequireUppercase = true;
                o.Password.RequireLowercase = true;
                o.Password.RequireNonAlphanumeric = false;
            })
            .AddRoles<IdentityRole<Guid>>()
            .AddEntityFrameworkStores<ApplicationDbContext>()
            .AddDefaultTokenProviders();

        services.AddValidatorsFromAssembly(typeof(FutureCV.Application.DependencyInjection).Assembly);
        services.AddScoped<IJwtTokenService, JwtTokenService>();
        var cookies = new StubTokenCookieService();
        services.AddSingleton(cookies);
        services.AddSingleton<ITokenCookieService>(cookies);
        services.AddSingleton<IEmailService, StubEmailService>();
        services.AddSingleton<IGoogleTokenValidator, StubGoogleTokenValidator>();
        services.AddScoped<IAuthService, AuthService>();

        return (services.BuildServiceProvider(), cookies);
    }

    [Fact]
    public async Task ChangePassword_VerifiesCurrentPassword_AndRevokesPriorSessions()
    {
        var (provider, _) = BuildAuthTestProvider();
        using var _ = provider;
        using var scope = provider.CreateScope();

        var roleManager = scope.ServiceProvider.GetRequiredService<RoleManager<IdentityRole<Guid>>>();
        await roleManager.CreateAsync(new IdentityRole<Guid>("Candidate"));
        var auth = scope.ServiceProvider.GetRequiredService<IAuthService>();

        var reg = await auth.RegisterCandidateAsync(new RegisterCandidateRequest
        {
            Email = "cand@example.com",
            Password = "OldPass123",
            ConfirmPassword = "OldPass123",
            FullName = "Candidate A",
        });
        Assert.True(reg.IsSuccess);

        var secondLogin = await auth.LoginAsync(new LoginRequest("cand@example.com", "OldPass123"));
        Assert.True(secondLogin.IsSuccess);

        var userManager = scope.ServiceProvider.GetRequiredService<UserManager<AppUser>>();
        var user = await userManager.FindByEmailAsync("cand@example.com");
        Assert.NotNull(user);

        var wrongCurrent = await auth.ChangePasswordAsync(
            user!.Id, new ChangePasswordRequest("WrongPass123", "NewPass456", "NewPass456"));
        Assert.False(wrongCurrent.IsSuccess);
        Assert.Equal("Current password is incorrect.", wrongCurrent.ErrorMessage);

        var changed = await auth.ChangePasswordAsync(
            user.Id, new ChangePasswordRequest("OldPass123", "NewPass456", "NewPass456"));
        Assert.True(changed.IsSuccess);

        // Fresh token returned by ChangePasswordAsync works
        var freshRefresh = await auth.RefreshTokenAsync(new RefreshTokenRequest { RefreshToken = changed.Data!.RefreshToken });
        Assert.True(freshRefresh.IsSuccess);

        // Prior refresh tokens from both sessions must be rejected
        var oldRefresh1 = await auth.RefreshTokenAsync(new RefreshTokenRequest { RefreshToken = reg.Data!.RefreshToken });
        var oldRefresh2 = await auth.RefreshTokenAsync(new RefreshTokenRequest { RefreshToken = secondLogin.Data!.RefreshToken });
        Assert.False(oldRefresh1.IsSuccess);
        Assert.False(oldRefresh2.IsSuccess);

        // Old password no longer logs in; new password works
        Assert.False((await auth.LoginAsync(new LoginRequest("cand@example.com", "OldPass123"))).IsSuccess);
        Assert.True((await auth.LoginAsync(new LoginRequest("cand@example.com", "NewPass456"))).IsSuccess);
    }

    [Fact]
    public async Task ResetPassword_RevokesAllExistingRefreshTokens()
    {
        var (provider, cookies) = BuildAuthTestProvider();
        using var _ = provider;
        using var scope = provider.CreateScope();

        var roleManager = scope.ServiceProvider.GetRequiredService<RoleManager<IdentityRole<Guid>>>();
        await roleManager.CreateAsync(new IdentityRole<Guid>("Candidate"));
        var auth = scope.ServiceProvider.GetRequiredService<IAuthService>();

        var session1 = await auth.RegisterCandidateAsync(new RegisterCandidateRequest
        {
            Email = "reset@example.com",
            Password = "OldPass123",
            ConfirmPassword = "OldPass123",
            FullName = "Reset User",
        });
        var session2 = await auth.LoginAsync(new LoginRequest("reset@example.com", "OldPass123"));
        Assert.True(session1.IsSuccess);
        Assert.True(session2.IsSuccess);

        var userManager = scope.ServiceProvider.GetRequiredService<UserManager<AppUser>>();
        var user = await userManager.FindByEmailAsync("reset@example.com");
        var resetToken = await userManager.GeneratePasswordResetTokenAsync(user!);

        var reset = await auth.ResetPasswordAsync(new ResetPasswordRequest(
            "reset@example.com", Uri.EscapeDataString(resetToken), "NewPass789", "NewPass789"));
        Assert.True(reset.IsSuccess);
        Assert.True(cookies.DeleteCount > 0);

        var refreshAfterReset1 = await auth.RefreshTokenAsync(new RefreshTokenRequest { RefreshToken = session1.Data!.RefreshToken });
        var refreshAfterReset2 = await auth.RefreshTokenAsync(new RefreshTokenRequest { RefreshToken = session2.Data!.RefreshToken });
        Assert.False(refreshAfterReset1.IsSuccess);
        Assert.False(refreshAfterReset2.IsSuccess);
    }

    [Fact]
    public async Task SampleJobsSeeder_Seeds500JobsIdempotently()
    {
        var (provider, _) = BuildAuthTestProvider();
        using var _ = provider;

        await ReferenceDataSeeder.SeedAsync(provider);

        using (var scope = provider.CreateScope())
        {
            var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
            var company = new Company { Name = "Seed Corp", TaxCode = "9999999999", VerifiedStatus = CompanyVerificationStatus.Verified };
            db.Companies.Add(company);
            await db.SaveChangesAsync();

            db.Employers.Add(new Employer { UserId = Guid.NewGuid(), CompanyId = company.Id, FullName = "Seed HR" });
            await db.SaveChangesAsync();
        }

        await SampleJobsSeeder.SeedAsync(provider, targetTotalJobs: 500);
        await SampleJobsSeeder.SeedAsync(provider, targetTotalJobs: 500);

        using (var verifyScope = provider.CreateScope())
        {
            var db = verifyScope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
            Assert.Equal(500, await db.Jobs.CountAsync());
            Assert.True(await db.JobSkills.CountAsync() >= 1500);
            Assert.All(await db.Jobs.Take(20).ToListAsync(), j =>
            {
                Assert.False(string.IsNullOrWhiteSpace(j.Title));
                Assert.False(string.IsNullOrWhiteSpace(j.Requirements));
                Assert.NotNull(j.CategoryId);
                Assert.NotNull(j.LocationId);
            });
        }
    }

    [Fact]
    public async Task HomeHighlights_CountsOnlyOpenApprovedJobs_AndSearchSupportsCompanyAndParentCategory()
    {
        using var db = CreateDbContext();
        var parentCat = new JobCategory { Id = Guid.NewGuid(), Name = "Công nghệ thông tin / Phần mềm" };
        var childCat = new JobCategory { Id = Guid.NewGuid(), Name = "Lập trình Backend", ParentId = parentCat.Id, Parent = parentCat };
        var companyA = new Company { Id = Guid.NewGuid(), Name = "MoMo Fintech", TaxCode = "0305196215", Industry = "Fintech", VerifiedStatus = CompanyVerificationStatus.Verified };
        var companyB = new Company { Id = Guid.NewGuid(), Name = "VNG Corp", TaxCode = "0309999999", Industry = "Internet", VerifiedStatus = CompanyVerificationStatus.Verified };
        db.JobCategories.AddRange(parentCat, childCat);
        db.Companies.AddRange(companyA, companyB);

        db.Jobs.AddRange(
            new Job { CompanyId = companyA.Id, PostedById = Guid.NewGuid(), Title = "Backend Dev", Description = "API", CategoryId = childCat.Id, ApprovalStatus = JobApprovalStatus.Approved, IsActive = true },
            new Job { CompanyId = companyA.Id, PostedById = Guid.NewGuid(), Title = "Data Engineer", Description = "ETL", CategoryId = parentCat.Id, ApprovalStatus = JobApprovalStatus.Approved, IsActive = true },
            // Closed & Pending jobs must NOT be counted
            new Job { CompanyId = companyA.Id, PostedById = Guid.NewGuid(), Title = "Closed Role", Description = "Closed", CategoryId = childCat.Id, ApprovalStatus = JobApprovalStatus.Approved, IsActive = false },
            new Job { CompanyId = companyB.Id, PostedById = Guid.NewGuid(), Title = "Pending Role", Description = "Pending", CategoryId = childCat.Id, ApprovalStatus = JobApprovalStatus.Pending, IsActive = true },
            new Job { CompanyId = companyB.Id, PostedById = Guid.NewGuid(), Title = "Open VNG Role", Description = "Cloud", CategoryId = childCat.Id, ApprovalStatus = JobApprovalStatus.Approved, IsActive = true });
        await db.SaveChangesAsync();

        var jobService = new JobService(db);
        var highlights = await jobService.GetHomeHighlightsAsync();
        Assert.True(highlights.IsSuccess);
        Assert.Equal(2, highlights.Data!.FeaturedCompanies.Count);
        Assert.Equal("MoMo Fintech", highlights.Data.FeaturedCompanies[0].Name);
        Assert.Equal(2, highlights.Data.FeaturedCompanies[0].OpenJobsCount);
        Assert.Equal(1, highlights.Data.FeaturedCompanies[1].OpenJobsCount);

        Assert.Single(highlights.Data.TopCategories);
        Assert.Equal(parentCat.Id, highlights.Data.TopCategories[0].Id);
        Assert.Equal(3, highlights.Data.TopCategories[0].OpenJobsCount);

        var byCompany = await jobService.SearchJobsAsync(new JobFilterRequest(Keyword: "MoMo"));
        Assert.True(byCompany.IsSuccess);
        Assert.Equal(2, byCompany.Data!.TotalCount);

        var byParentCategory = await jobService.SearchJobsAsync(new JobFilterRequest(CategoryId: parentCat.Id));
        Assert.True(byParentCategory.IsSuccess);
        Assert.Equal(3, byParentCategory.Data!.TotalCount);
    }
}
