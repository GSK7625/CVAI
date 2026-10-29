using System.Text.Json;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.AiMatching.Configurations;
using FutureCV.Application.Features.AiMatching.DTOs;
using FutureCV.Infrastructure.Configurations;
using FutureCV.Application.Features.Candidate.DTOs;
using FutureCV.Application.Features.JobApplication.DTOs;
using FutureCV.Application.Features.JobApplication.Services;
using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;
using FutureCV.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using Xunit;

namespace FutureCV.Domain.Tests.IntegrationTests;

public class PreviewJobMatchShadowIntegrationTests
{
    private sealed class TestAiMatchingClient : IAiMatchingClient
    {
        public int CallCount { get; private set; }
        public AiMatchRequest? LastRequest { get; private set; }
        public Func<AiMatchRequest, Task<ServiceResult<AiMatchResultDto>>>? Handler { get; set; }

        public async Task<ServiceResult<AiMatchResultDto>> MatchAsync(
            AiMatchRequest request,
            string? correlationId = null,
            CancellationToken cancellationToken = default)
        {
            CallCount++;
            LastRequest = request;

            if (Handler != null)
            {
                return await Handler(request);
            }

            return ServiceResult.Success(new AiMatchResultDto(
                MatchScore: 95,
                MatchedSkills: ["AI Matched Skill"],
                MissingSkills: ["AI Missing Skill"],
                ExperienceComparison: "AI Experience Comparison",
                EducationComparison: "AI Education Comparison",
                ProjectDomainRelevance: "AI Project Relevance",
                MatchExplanation: "AI Match Explanation",
                Meta: new AiResponseMetaDto(
                    AlgorithmVersion: "test-v1",
                    ContractVersion: "match-result-v1",
                    CorrelationId: "test-corr-id"
                )
            ));
        }
    }

    private sealed class TestIdentityService : IIdentityService
    {
        public Task<string?> GetUserEmailAsync(Guid userId, CancellationToken cancellationToken = default)
            => Task.FromResult<string?>("candidate@example.com");

        public Task<PagedResult<FutureCV.Application.Common.Models.IdentityUserInfo>> GetUsersAsync(
            FutureCV.Application.Features.Admin.DTOs.UserQueryFilter filter, CancellationToken cancellationToken = default)
            => Task.FromResult(new PagedResult<FutureCV.Application.Common.Models.IdentityUserInfo>([], 0, 1, 10));

        public Task<ServiceResult<bool>> LockUserAsync(Guid targetUserId, CancellationToken cancellationToken = default)
            => Task.FromResult(ServiceResult.Success(true));

        public Task<ServiceResult<bool>> UnlockUserAsync(Guid targetUserId, CancellationToken cancellationToken = default)
            => Task.FromResult(ServiceResult.Success(true));

        public Task<FutureCV.Application.Features.Admin.DTOs.AdminUserStatsDto> GetUserStatsAsync(CancellationToken cancellationToken = default)
            => Task.FromResult(new FutureCV.Application.Features.Admin.DTOs.AdminUserStatsDto(0, 0, 0, 0, 0));
    }

    private static ApplicationDbContext CreateDbContext()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;
        return new ApplicationDbContext(options);
    }

    private static (Guid userId, Guid jobId, Guid cvId) SeedStandardScenario(
        ApplicationDbContext db,
        string? parsedDataJson = null,
        bool createParser = true)
    {
        var userId = Guid.NewGuid();
        var candidateId = Guid.NewGuid();
        var jobId = Guid.NewGuid();
        var cvId = Guid.NewGuid();
        var companyId = Guid.NewGuid();

        var skillCSharp = new Skill { Id = Guid.NewGuid(), Name = "C#" };
        var skillDotNet = new Skill { Id = Guid.NewGuid(), Name = ".NET" };
        var skillSql = new Skill { Id = Guid.NewGuid(), Name = "SQL" };
        db.Skills.AddRange(skillCSharp, skillDotNet, skillSql);

        var candidate = new Candidate
        {
            Id = candidateId,
            UserId = userId,
            FullName = "Nguyen Van A",
            Summary = "Profile Summary",
            CVs =
            [
                new CandidateCv
                {
                    Id = cvId,
                    CandidateId = candidateId,
                    Title = "Backend CV",
                    IsDeleted = false,
                    CreatedAt = DateTime.UtcNow
                }
            ],
            Skills =
            [
                new CandidateSkill { CandidateId = candidateId, SkillId = skillCSharp.Id, Skill = skillCSharp }
            ]
        };
        db.Candidates.Add(candidate);

        var job = new Job
        {
            Id = jobId,
            CompanyId = companyId,
            PostedById = Guid.NewGuid(),
            Title = "Senior .NET Developer",
            Description = "We are hiring a senior .NET dev",
            IsActive = true,
            ApprovalStatus = JobApprovalStatus.Approved,
            JobSkills =
            [
                new JobSkill { JobId = jobId, SkillId = skillCSharp.Id, Skill = skillCSharp, IsRequired = true },
                new JobSkill { JobId = jobId, SkillId = skillDotNet.Id, Skill = skillDotNet, IsRequired = true }
            ]
        };
        db.Jobs.Add(job);

        if (createParser)
        {
            var defaultStructuredCv = new StructuredCvDataDto(
                FullName: "Nguyen Van A",
                Email: "a@example.com",
                Phone: "0901234567",
                Summary: "CV Summary",
                Skills: ["C#", ".NET"],
                Experiences: [
                    new CvExperienceDto("Tech Corp", "Software Engineer", new DateOnly(2022, 1, 1), null, true, "Dev")
                ],
                Educations: [
                    new CvEducationDto("Univ", "Bachelor", "CS", 2018, 2022, null)
                ],
                Projects: [
                    new CvProjectDto("Core API", "Backend", null, null, false, "Desc", "C#")
                ]
            );

            var parser = new CvParser
            {
                CvId = cvId,
                ParsedDataJson = parsedDataJson ?? JsonSerializer.Serialize(defaultStructuredCv)
            };
            db.CvParsers.Add(parser);
        }

        db.SaveChanges();
        return (userId, jobId, cvId);
    }

    // =========================================================================
    // Scenario A: Shadow Mode Disabled
    // =========================================================================
    [Fact]
    public async Task PreviewJobMatch_WhenShadowDisabled_DoesNotCallAiMatchingClient_AndReturnsLegacyResult()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = false });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(0, aiClient.CallCount); // Zero AI calls
        Assert.Equal(50, result.Data.MatchScore); // Legacy rule: 30% skills + 10% neutral location + 10% neutral salary = 50%
    }

    // =========================================================================
    // Scenario B & C: Shadow Mode Enabled + Structured CV Ready
    // =========================================================================
    [Fact]
    public async Task PreviewJobMatch_WhenShadowEnabled_CallsAiClientOnce_WithSelectedCvData_AndDoesNotAlterLegacyResponse()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = true });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        // 1. Assert service succeeded
        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);

        // 2. Assert AI Matching Client was invoked exactly once
        Assert.Equal(1, aiClient.CallCount);
        Assert.NotNull(aiClient.LastRequest);
        Assert.Equal("Nguyen Van A", aiClient.LastRequest.Cv.FullName);
        Assert.Equal("Senior .NET Developer", aiClient.LastRequest.Job.Title);
        Assert.Contains("C#", aiClient.LastRequest.Cv.Skills);

        // 3. Assert AI score (95) did NOT replace legacy score (50 = 30 skill + 10 loc + 10 sal)
        Assert.NotEqual(95, result.Data.MatchScore);
        Assert.Contains("C#", result.Data.MatchedSkills);
        Assert.DoesNotContain("AI Matched Skill", result.Data.MatchedSkills);

        // 4. Assert no DB mutations occurred
        Assert.Empty(db.Applications);
    }

    // =========================================================================
    // Scenario D: Shadow Mode Enabled + AI Failure
    // =========================================================================
    [Fact]
    public async Task PreviewJobMatch_WhenAiServiceFails_PreviewStillSucceeds_ReturningLegacyResponse()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient
        {
            Handler = _ => Task.FromResult(ServiceResult.Failure<AiMatchResultDto>(
                "Python AI service 500 Internal Error", ServiceErrorType.Infrastructure))
        };
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = true });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(1, aiClient.CallCount);
        Assert.Equal(cvId, result.Data.CvId);
    }

    // =========================================================================
    // Scenario E: Shadow Mode Enabled + AI Timeout vs Caller Cancellation
    // =========================================================================
    [Fact]
    public async Task PreviewJobMatch_WhenAiTimesOut_PreviewStillSucceeds_UnlessCallerWasCancelled()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient
        {
            Handler = _ => throw new TimeoutException("HTTP client timeout calling FastAPI")
        };
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = true });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        // AI timeout without caller cancellation must NOT fail preview
        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
    }

    [Fact]
    public async Task PreviewJobMatch_WhenCallerCancels_PreservesCancellationSemantics()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        using var cts = new CancellationTokenSource();
        cts.Cancel(); // Caller cancelled request

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = true });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        await Assert.ThrowsAnyAsync<OperationCanceledException>(async () =>
        {
            await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId), cts.Token);
        });
    }

    // =========================================================================
    // Scenario F: Shadow Mode Enabled + Selected CV Not Parsed
    // =========================================================================
    [Fact]
    public async Task PreviewJobMatch_WhenSelectedCvHasNoParser_SkipsAiCall_AndReturnsLegacyResult()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db, createParser: false);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = true });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(0, aiClient.CallCount); // Skipped because CV is not parsed
    }

    // =========================================================================
    // Scenario G: Shadow Mode Enabled + Malformed ParsedDataJson
    // =========================================================================
    [Fact]
    public async Task PreviewJobMatch_WhenParsedDataJsonIsMalformed_SkipsAiCall_AndReturnsLegacyResult()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db, parsedDataJson: "{ NOT VALID JSON ");

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = true });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(0, aiClient.CallCount); // Skipped because JSON is malformed
    }

    // =========================================================================
    // Scenario H: Multiple CVs — Only Selected CvId Is Sent To AI
    // =========================================================================
    [Fact]
    public async Task PreviewJobMatch_WithMultipleCvs_UsesOnlyTheSelectedCvId()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cv1Id) = SeedStandardScenario(db);

        var candidate = await db.Candidates.AsNoTracking().FirstAsync(c => c.UserId == userId);
        var cv2Id = Guid.NewGuid();
        db.CandidateCvs.Add(new CandidateCv
        {
            Id = cv2Id,
            CandidateId = candidate.Id,
            Title = "Python CV",
            IsDeleted = false,
            CreatedAt = DateTime.UtcNow
        });

        var cv2StructuredData = new StructuredCvDataDto(
            FullName: "Nguyen Van A - Python Profile",
            Email: "python@example.com",
            Phone: "0999999999",
            Summary: "Python specialist",
            Skills: ["Python", "FastAPI"],
            Experiences: [],
            Educations: [],
            Projects: []
        );

        db.CvParsers.Add(new CvParser
        {
            CvId = cv2Id,
            ParsedDataJson = JsonSerializer.Serialize(cv2StructuredData)
        });
        db.SaveChanges();

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = true });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        // Explicitly select CV2
        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cv2Id));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(cv2Id, result.Data.CvId);
        Assert.Equal(1, aiClient.CallCount);
        Assert.NotNull(aiClient.LastRequest);
        Assert.Equal("Nguyen Van A - Python Profile", aiClient.LastRequest.Cv.FullName);
        Assert.Contains("FastAPI", aiClient.LastRequest.Cv.Skills);
        Assert.DoesNotContain("C#", aiClient.LastRequest.Cv.Skills); // CV1 data was NOT sent
    }

    // =========================================================================
    // Scenario I: No Candidate Profile Fallback
    // =========================================================================
    [Fact]
    public async Task PreviewJobMatch_NeverSubstitutesCandidateProfileSkillsIntoAiRequest()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        // Candidate Profile has skills: ["Java", "Spring Boot"]
        var candidate = await db.Candidates.Include(c => c.Skills).FirstAsync(c => c.UserId == userId);
        candidate.Skills.Clear();
        var javaSkill = new Skill { Id = Guid.NewGuid(), Name = "Java" };
        var springSkill = new Skill { Id = Guid.NewGuid(), Name = "Spring Boot" };
        db.Skills.AddRange(javaSkill, springSkill);
        candidate.Skills.Add(new CandidateSkill { CandidateId = candidate.Id, SkillId = javaSkill.Id, Skill = javaSkill });
        candidate.Skills.Add(new CandidateSkill { CandidateId = candidate.Id, SkillId = springSkill.Id, Skill = springSkill });

        // Selected CV structured data has skills: ["C#", ".NET"]
        var cvStructuredData = new StructuredCvDataDto(
            FullName: "Candidate Name",
            Email: "cv@example.com",
            Phone: "0912345678",
            Summary: null,
            Skills: ["C#", ".NET"],
            Experiences: [],
            Educations: [],
            Projects: []
        );

        var parser = await db.CvParsers.FirstAsync(p => p.CvId == cvId);
        parser.ParsedDataJson = JsonSerializer.Serialize(cvStructuredData);
        db.SaveChanges();

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = true });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.Equal(1, aiClient.CallCount);
        Assert.NotNull(aiClient.LastRequest);

        // AI Request contains ONLY the CV skills ["C#", ".NET"]
        Assert.Contains("C#", aiClient.LastRequest.Cv.Skills);
        Assert.Contains(".NET", aiClient.LastRequest.Cv.Skills);
        // AI Request MUST NOT contain Candidate Profile skills
        Assert.DoesNotContain("Java", aiClient.LastRequest.Cv.Skills);
        Assert.DoesNotContain("Spring Boot", aiClient.LastRequest.Cv.Skills);
    }

    // =========================================================================
    // Section 16: Verification That Other Application Flows Remain Unchanged
    // =========================================================================
    [Fact]
    public async Task ApplyJobAsync_NeverCallsAiMatchingClient_EvenWhenShadowEnabled()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = true });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var applyRequest = new ApplyJobRequest(cvId, "Cover letter text");
        var result = await service.ApplyJobAsync(userId, jobId, applyRequest);

        Assert.True(result.IsSuccess);
        Assert.Equal(0, aiClient.CallCount); // IAiMatchingClient MUST NOT be called in ApplyJobAsync
    }

    [Fact]
    public async Task GetJobSuggestionsAsync_NeverCallsAiMatchingClient_EvenWhenShadowEnabled()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions { PreviewShadowEnabled = true });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var filter = new JobSuggestionFilterRequest();
        var result = await service.GetJobSuggestionsAsync(userId, filter);

        Assert.True(result.IsSuccess);
        Assert.Equal(0, aiClient.CallCount); // IAiMatchingClient MUST NOT be called in GetJobSuggestionsAsync
    }

    // =========================================================================
    // Section 19: Options Architecture Cleanup & Decoupling Verification
    // =========================================================================
    [Fact]
    public void AiMatchingFeatureOptions_Defaults_PreviewShadowEnabledIsFalse()
    {
        var options = new AiMatchingFeatureOptions();
        Assert.False(options.PreviewShadowEnabled);
        Assert.Equal("AiMatching", AiMatchingFeatureOptions.SectionName);
    }

    [Fact]
    public void ApplicationService_Constructor_UsesAiMatchingFeatureOptionsOnly()
    {
        var constructor = typeof(ApplicationService).GetConstructors().Single();
        var parameters = constructor.GetParameters();

        // Parameter aiOptions must be IOptions<AiMatchingFeatureOptions>
        var optionsParam = parameters.FirstOrDefault(p => p.Name == "aiOptions");
        Assert.NotNull(optionsParam);
        Assert.Equal(typeof(IOptions<AiMatchingFeatureOptions>), optionsParam.ParameterType);

        // ApplicationService MUST NOT accept AiServiceOptions in any constructor parameter
        Assert.DoesNotContain(parameters, p => p.ParameterType.ToString().Contains("AiServiceOptions"));
    }

    [Fact]
    public void AiServiceOptions_IsInfrastructureOnlyTransportConfig_DoesNotContainFeatureFlag()
    {
        var properties = typeof(AiServiceOptions).GetProperties();
        Assert.Equal("AiService", AiServiceOptions.SectionName);
        Assert.Contains(properties, p => p.Name == nameof(AiServiceOptions.BaseUrl));
        Assert.Contains(properties, p => p.Name == nameof(AiServiceOptions.ApiKey));
        Assert.Contains(properties, p => p.Name == nameof(AiServiceOptions.TimeoutSeconds));

        // Transport options MUST NOT contain application-level feature flag
        Assert.DoesNotContain(properties, p => p.Name == "PreviewShadowEnabled");
    }

    [Fact]
    public void NoInheritanceExistsBetween_AiServiceOptions_And_AiMatchingFeatureOptions()
    {
        Assert.False(typeof(AiServiceOptions).IsSubclassOf(typeof(AiMatchingFeatureOptions)));
        Assert.False(typeof(AiMatchingFeatureOptions).IsSubclassOf(typeof(AiServiceOptions)));
        Assert.True(typeof(AiMatchingFeatureOptions).IsSealed);
        Assert.True(typeof(AiServiceOptions).IsSealed);
    }
}
