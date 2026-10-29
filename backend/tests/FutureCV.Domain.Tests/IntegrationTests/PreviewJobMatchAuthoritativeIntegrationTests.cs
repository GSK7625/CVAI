using System.Text.Json;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.AiMatching.Configurations;
using FutureCV.Application.Features.AiMatching.DTOs;
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

public class PreviewJobMatchAuthoritativeIntegrationTests
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
                MatchScore: 92,
                MatchedSkills: ["C#", ".NET"],
                MissingSkills: ["GraphQL"],
                ExperienceComparison: "5 years experience matches requirement.",
                EducationComparison: "BS Computer Science meets degree requirement.",
                ProjectDomainRelevance: "Relevant fintech background.",
                MatchExplanation: "Candidate is a strong match with solid .NET background.",
                Meta: new AiResponseMetaDto(
                    AlgorithmVersion: "authoritative-v1",
                    ContractVersion: "match-result-v1",
                    CorrelationId: "test-auth-corr-id"
                )
            ));
        }
    }

    private sealed class TestIdentityService : IIdentityService
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

    // TEST 1: PreviewAiEnabled=false, PreviewShadowEnabled=false -> legacy response, AI client not called
    [Fact]
    public async Task Test1_PreviewAiDisabled_And_ShadowDisabled_ReturnsLegacyResponse_AiNotCalled()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions
        {
            PreviewAiEnabled = false,
            PreviewShadowEnabled = false
        });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(0, aiClient.CallCount);
        Assert.Equal(50, result.Data.MatchScore); // Legacy score
    }

    // TEST 2: PreviewAiEnabled=true, AI success -> AI client called exactly once, AI score, matchedSkills, missingSkills, explanation
    [Fact]
    public async Task Test2_PreviewAiEnabled_OnAiSuccess_ReturnsAiResultAuthoritatively()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions
        {
            PreviewAiEnabled = true,
            PreviewShadowEnabled = false
        });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(1, aiClient.CallCount);
        Assert.Equal(92, result.Data.MatchScore); // AI score replaces legacy score
        Assert.Equal(["C#", ".NET"], result.Data.MatchedSkills);
        Assert.Equal(["GraphQL"], result.Data.MissingSkills);
        Assert.Equal("Candidate is a strong match with solid .NET background.", result.Data.Explanation);
        Assert.Equal(jobId, result.Data.JobId);
        Assert.Equal(cvId, result.Data.CvId);
        Assert.True(result.Data.LocationMatched);
        Assert.True(result.Data.SalaryMatched);
    }

    // TEST 3: PreviewAiEnabled=true, AI failure -> preview still succeeds, legacy result returned
    [Fact]
    public async Task Test3_PreviewAiEnabled_OnAiFailure_FallsBackToLegacyResult()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient
        {
            Handler = _ => Task.FromResult(ServiceResult.Failure<AiMatchResultDto>(
                "Service Unavailable", ServiceErrorType.Infrastructure))
        };
        var options = Options.Create(new AiMatchingFeatureOptions
        {
            PreviewAiEnabled = true,
            PreviewShadowEnabled = false
        });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(1, aiClient.CallCount);
        Assert.Equal(50, result.Data.MatchScore); // Falls back to legacy score
    }

    // TEST 4: PreviewAiEnabled=true, CV not parsed -> AI not called, legacy result returned
    [Fact]
    public async Task Test4_PreviewAiEnabled_WhenCvNotParsed_SkipsAiCall_ReturnsLegacyResult()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db, createParser: false);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions
        {
            PreviewAiEnabled = true,
            PreviewShadowEnabled = false
        });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(0, aiClient.CallCount); // Never called
        Assert.Equal(50, result.Data.MatchScore); // Legacy score
    }

    // TEST 5: PreviewAiEnabled=true, malformed ParsedDataJson -> legacy result returned
    [Fact]
    public async Task Test5_PreviewAiEnabled_WhenParsedDataJsonMalformed_SkipsAiCall_ReturnsLegacyResult()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db, parsedDataJson: "{ MALFORMED JSON !!!");

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions
        {
            PreviewAiEnabled = true,
            PreviewShadowEnabled = false
        });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(0, aiClient.CallCount);
        Assert.Equal(50, result.Data.MatchScore); // Legacy score
    }

    // TEST 6: PreviewAiEnabled=true + PreviewShadowEnabled=true -> AI authoritative mode wins, exactly one call
    [Fact]
    public async Task Test6_PreviewAiEnabled_TakesPrecedenceOver_PreviewShadowEnabled_CallsAiOnce()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions
        {
            PreviewAiEnabled = true,
            PreviewShadowEnabled = true
        });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var result = await service.PreviewJobMatchAsync(userId, jobId, new PreviewJobMatchRequest(cvId));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(1, aiClient.CallCount); // Exactly 1 AI call (no duplicate shadow call)
        Assert.Equal(92, result.Data.MatchScore); // AI score returned
    }

    // TEST 7: ApplyJobAsync -> AI client never called
    [Fact]
    public async Task Test7_ApplyJobAsync_NeverCallsAiMatchingClient_EvenWhenPreviewAiEnabled()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions
        {
            PreviewAiEnabled = true,
            PreviewShadowEnabled = true
        });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var applyRequest = new ApplyJobRequest(cvId, "Cover letter text");
        var result = await service.ApplyJobAsync(userId, jobId, applyRequest);

        Assert.True(result.IsSuccess);
        Assert.Equal(0, aiClient.CallCount); // AI client NEVER called
    }

    // TEST 8: GetJobSuggestionsAsync -> AI client never called
    [Fact]
    public async Task Test8_GetJobSuggestionsAsync_NeverCallsAiMatchingClient_EvenWhenPreviewAiEnabled()
    {
        using var db = CreateDbContext();
        var (userId, jobId, cvId) = SeedStandardScenario(db);

        var aiClient = new TestAiMatchingClient();
        var options = Options.Create(new AiMatchingFeatureOptions
        {
            PreviewAiEnabled = true,
            PreviewShadowEnabled = true
        });
        var service = new ApplicationService(db, new TestIdentityService(), aiClient, options, NullLogger<ApplicationService>.Instance);

        var filter = new JobSuggestionFilterRequest();
        var result = await service.GetJobSuggestionsAsync(userId, filter);

        Assert.True(result.IsSuccess);
        Assert.Equal(0, aiClient.CallCount); // AI client NEVER called
    }
}

