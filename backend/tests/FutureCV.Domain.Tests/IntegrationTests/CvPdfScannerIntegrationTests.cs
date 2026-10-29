using System.Text.Json;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Candidate.DTOs;
using FutureCV.Application.Features.Candidate.Services;
using FutureCV.Domain.Entities;
using FutureCV.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace FutureCV.Domain.Tests.IntegrationTests;

public class CvPdfScannerIntegrationTests
{
    private sealed class TestFileStorage : IFileStorage
    {
        public Task<(string PublicUrl, string PublicId)> UploadAsync(
            Stream fileStream, string fileName, string folder, CancellationToken cancellationToken = default)
            => Task.FromResult(("https://res.cloudinary.com/dummy/cv.pdf", "cv-public-id-123"));

        public Task<(string PublicUrl, string PublicId)> UploadDocumentAsync(
            Stream fileStream, string fileName, string folder, CancellationToken cancellationToken = default)
            => Task.FromResult(("https://res.cloudinary.com/dummy/cv.pdf", "cv-public-id-123"));

        public Task DeleteAsync(string publicId, CancellationToken cancellationToken = default)
            => Task.CompletedTask;

        public Task DeleteDocumentAsync(string publicId, CancellationToken cancellationToken = default)
            => Task.CompletedTask;
    }

    private sealed class TestIdentityService : IIdentityService
    {
        public Task<string?> GetUserEmailAsync(Guid userId, CancellationToken cancellationToken = default)
            => Task.FromResult<string?>("minh.khoa.dev@gmail.com");

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

    private sealed class TestAiCvClient : IAiCvClient
    {
        public int AnalyzePdfCallCount { get; private set; }
        public int AnalyzeTextCallCount { get; private set; }
        public Func<byte[], string, Task<ServiceResult<FastApiCvAnalysisResponseDto>>>? PdfHandler { get; set; }
        public Func<string, Task<ServiceResult<FastApiCvAnalysisResponseDto>>>? TextHandler { get; set; }

        public async Task<ServiceResult<FastApiCvAnalysisResponseDto>> AnalyzePdfAsync(
            byte[] fileBytes,
            string fileName,
            string? correlationId = null,
            CancellationToken cancellationToken = default)
        {
            AnalyzePdfCallCount++;
            if (PdfHandler != null)
                return await PdfHandler(fileBytes, fileName);

            return ServiceResult.Success(new FastApiCvAnalysisResponseDto(
                StructuredCv: new FastApiStructuredCvDto(
                    FullName: "NGUYEN MINH KHOA",
                    Email: "minh.khoa.dev@gmail.com",
                    Phone: "+84 912 345 678",
                    CareerSummary: "Senior .NET Backend Engineer with 6+ years experience.",
                    Skills: [".NET", "C#", "PostgreSQL"],
                    WorkExperience: [
                        new FastApiWorkExperienceDto(
                            JobTitle: "Senior Backend Engineer",
                            Company: "FPT Software",
                            Duration: "03/2022 - Present",
                            StartDate: "2022-03",
                            EndDate: null,
                            YearsOfExperience: 6.0,
                            Description: "Built microservices using .NET and PostgreSQL."
                        )
                    ],
                    Education: [
                        new FastApiEducationDto(
                            Degree: "Bachelor",
                            Institution: "HUST",
                            FieldOfStudy: "Computer Science",
                            GraduationYear: "2019"
                        )
                    ],
                    Certificates: [],
                    Projects: [
                        new FastApiProjectDto(
                            Name: "Microservices Platform",
                            Description: "High-scale backend",
                            Technologies: [".NET", "Docker"]
                        )
                    ],
                    Technologies: ["Docker", "Redis"]
                ),
                CvScore: 95,
                Strengths: ["Strong technical foundation in .NET and PostgreSQL"],
                Weaknesses: ["Could add more business impact metrics"],
                ImprovementSuggestions: ["Include quantified results in project descriptions"],
                RawText: "Raw CV text content for testing"
            ));
        }

        public async Task<ServiceResult<FastApiCvAnalysisResponseDto>> AnalyzeTextAsync(
            string rawText,
            string? candidateId = null,
            string? correlationId = null,
            CancellationToken cancellationToken = default)
        {
            AnalyzeTextCallCount++;
            if (TextHandler != null)
                return await TextHandler(rawText);

            return ServiceResult.Success(new FastApiCvAnalysisResponseDto(
                StructuredCv: null,
                CvScore: 90,
                Strengths: ["Good presentation"],
                Weaknesses: [],
                ImprovementSuggestions: [],
                RawText: rawText
            ));
        }
    }

    private static ApplicationDbContext CreateDbContext()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(databaseName: $"FutureCv_CvScannerTest_{Guid.NewGuid()}")
            .Options;

        return new ApplicationDbContext(options);
    }

    [Fact]
    public async Task UploadCvAsync_WhenAiClientSucceeds_AutomaticallyScansAndSetsParsedStatus()
    {
        // Arrange
        using var context = CreateDbContext();
        var userId = Guid.NewGuid();
        var candidate = new Candidate
        {
            Id = Guid.NewGuid(),
            UserId = userId,
            FullName = "Nguyen Minh Khoa"
        };
        context.Candidates.Add(candidate);
        await context.SaveChangesAsync();

        var aiClient = new TestAiCvClient();
        var service = new CandidateService(
            context,
            new TestFileStorage(),
            new TestIdentityService(),
            aiClient,
            NullLogger<CandidateService>.Instance);

        var dummyPdfBytes = "%PDF-1.4 dummy pdf content for testing"u8.ToArray();
        using var stream = new MemoryStream(dummyPdfBytes);
        var fileUpload = new FileUploadRequest(stream, "MinhKhoa_CV.pdf", "application/pdf", dummyPdfBytes.Length);

        // Act
        var result = await service.UploadCvAsync(userId, fileUpload, "Minh Khoa CV");

        // Assert
        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(1, aiClient.AnalyzePdfCallCount);

        var cvInDb = await context.CandidateCvs.FirstOrDefaultAsync(c => c.Id == result.Data.Id);
        Assert.NotNull(cvInDb);
        Assert.Equal("Parsed", cvInDb.ParseStatus);

        // Verify CvParser created in DB
        var parser = await context.CvParsers.FirstOrDefaultAsync(p => p.CvId == result.Data.Id);
        Assert.NotNull(parser);
        Assert.Equal("AI-v1", parser.ModelVersion);
        Assert.False(string.IsNullOrWhiteSpace(parser.ParsedDataJson));

        var parsedData = JsonSerializer.Deserialize<StructuredCvDataDto>(parser.ParsedDataJson!);
        Assert.NotNull(parsedData);
        Assert.Equal("NGUYEN MINH KHOA", parsedData.FullName);
        Assert.Contains("C#", parsedData.Skills);
        Assert.Contains(".NET", parsedData.Skills);
        Assert.Contains("PostgreSQL", parsedData.Skills);
        Assert.Contains("Docker", parsedData.Skills);

        // Verify CvEvaluation created in DB
        var evaluation = await context.CvEvaluations.FirstOrDefaultAsync(e => e.CvId == result.Data.Id);
        Assert.NotNull(evaluation);
        Assert.Equal(95, evaluation.CvScore);
        Assert.Contains("Strong technical foundation", evaluation.StrengthsJson);
    }

    [Fact]
    public async Task UploadCvAsync_WhenAiClientFails_GracefullyFallsBackToPendingStatus()
    {
        // Arrange
        using var context = CreateDbContext();
        var userId = Guid.NewGuid();
        var candidate = new Candidate
        {
            Id = Guid.NewGuid(),
            UserId = userId,
            FullName = "Fallback Candidate"
        };
        context.Candidates.Add(candidate);
        await context.SaveChangesAsync();

        var aiClient = new TestAiCvClient
        {
            PdfHandler = (_, _) => Task.FromResult(
                ServiceResult.Failure<FastApiCvAnalysisResponseDto>("FastAPI unavailable", ServiceErrorType.Infrastructure))
        };

        var service = new CandidateService(
            context,
            new TestFileStorage(),
            new TestIdentityService(),
            aiClient,
            NullLogger<CandidateService>.Instance);

        var dummyPdfBytes = "%PDF-1.4 dummy"u8.ToArray();
        using var stream = new MemoryStream(dummyPdfBytes);
        var fileUpload = new FileUploadRequest(stream, "cv.pdf", "application/pdf", dummyPdfBytes.Length);

        // Act
        var result = await service.UploadCvAsync(userId, fileUpload, "My CV");

        // Assert - Upload still succeeds!
        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(1, aiClient.AnalyzePdfCallCount);

        var cvInDb = await context.CandidateCvs.FirstOrDefaultAsync(c => c.Id == result.Data.Id);
        Assert.NotNull(cvInDb);
        Assert.Equal("Pending", cvInDb.ParseStatus);

        // Parser was not created
        var parser = await context.CvParsers.FirstOrDefaultAsync(p => p.CvId == result.Data.Id);
        Assert.Null(parser);
    }

    [Fact]
    public void FastApiCvMapper_MapsToStructuredCvDataDto_Correctly()
    {
        // Arrange
        var fastApiCv = new FastApiStructuredCvDto(
            FullName: "Tran Van B",
            Email: "b@example.com",
            Phone: "0987654321",
            CareerSummary: "Fullstack Engineer",
            Skills: [".NET", "C#", "SQL"],
            WorkExperience: [
                new FastApiWorkExperienceDto(
                    JobTitle: "Lead Dev",
                    Company: "Tech Corp",
                    Duration: "2020 - Present",
                    StartDate: "2020-01",
                    EndDate: null,
                    YearsOfExperience: 4.0,
                    Description: "Led engineering team"
                )
            ],
            Education: [
                new FastApiEducationDto(
                    Degree: "BS",
                    Institution: "Tech Univ",
                    FieldOfStudy: "IT",
                    GraduationYear: "2020"
                )
            ],
            Certificates: [],
            Projects: [
                new FastApiProjectDto(
                    Name: "Fintech App",
                    Description: "Payment gateway",
                    Technologies: ["C#", "Docker"]
                )
            ],
            Technologies: ["Docker", "Kubernetes"]
        );

        // Act
        var structuredDto = FastApiCvMapper.ToStructuredCvDataDto(fastApiCv);

        // Assert
        Assert.Equal("Tran Van B", structuredDto.FullName);
        Assert.Equal("b@example.com", structuredDto.Email);
        Assert.Equal("0987654321", structuredDto.Phone);
        Assert.Equal("Fullstack Engineer", structuredDto.Summary);
        Assert.Contains(".NET", structuredDto.Skills);
        Assert.Contains("C#", structuredDto.Skills);
        Assert.Contains("SQL", structuredDto.Skills);
        Assert.Contains("Docker", structuredDto.Skills);
        Assert.Contains("Kubernetes", structuredDto.Skills);

        Assert.Single(structuredDto.Experiences);
        Assert.True(structuredDto.Experiences[0].IsCurrent);
        Assert.Equal(new DateOnly(2020, 1, 1), structuredDto.Experiences[0].StartDate);

        Assert.Single(structuredDto.Educations);
        Assert.Equal(2020, structuredDto.Educations[0].EndYear);

        Assert.Single(structuredDto.Projects);
        Assert.Equal("Fintech App", structuredDto.Projects[0].Name);
        Assert.Contains("Docker", structuredDto.Projects[0].Technologies);
    }

    [Fact]
    public void FastApiCvMapper_WithMissingDates_OmitsExperienceWithoutArbitraryTwoYearsFallback()
    {
        // Arrange: Experience without StartDate, and experience without EndDate (not containing present)
        var fastApiCv = new FastApiStructuredCvDto(
            FullName: "Nguyen Van A",
            Email: null,
            Phone: null,
            CareerSummary: null,
            Skills: [],
            WorkExperience: [
                new FastApiWorkExperienceDto(
                    JobTitle: "Role Without Start Date",
                    Company: "Company Without Date",
                    Duration: "",
                    StartDate: null,
                    EndDate: null,
                    YearsOfExperience: 0.0,
                    Description: "No date recorded"
                ),
                new FastApiWorkExperienceDto(
                    JobTitle: "Past Engineer",
                    Company: "Previous Co",
                    Duration: "2021 - 2022",
                    StartDate: "2021-01",
                    EndDate: null,
                    YearsOfExperience: 1.0,
                    Description: "Past role where EndDate is null but duration is not ongoing"
                )
            ],
            Education: [],
            Certificates: [],
            Projects: [],
            Technologies: []
        );

        // Act
        var structuredDto = FastApiCvMapper.ToStructuredCvDataDto(fastApiCv);

        // Assert:
        // 1. The experience with null StartDate MUST be omitted (no arbitrary AddYears(-2) fallback)
        Assert.Single(structuredDto.Experiences);
        var exp = structuredDto.Experiences[0];
        Assert.Equal("Past Engineer", exp.Position);
        Assert.Equal(new DateOnly(2021, 1, 1), exp.StartDate);

        // 2. Since EndDate is null and Duration does not say "present/hiện tại/nay", IsCurrent must be FALSE
        Assert.False(exp.IsCurrent);
        Assert.Null(exp.EndDate);
    }

    [Fact]
    public void FastApiCvMapper_WithMissingPlaceholders_DoesNotSynthesizeCompanyOrUniversityOrProject()
    {
        // Arrange
        var fastApiCv = new FastApiStructuredCvDto(
            FullName: null,
            Email: null,
            Phone: null,
            CareerSummary: null,
            Skills: [],
            WorkExperience: [
                new FastApiWorkExperienceDto(
                    JobTitle: "Solo Freelancer",
                    Company: null,
                    Duration: "2022-01 - 2023-01",
                    StartDate: "2022-01",
                    EndDate: "2023-01",
                    YearsOfExperience: 1.0,
                    Description: "Independent work"
                )
            ],
            Education: [
                new FastApiEducationDto(
                    Degree: "Self-taught Engineer",
                    Institution: null,
                    FieldOfStudy: null,
                    GraduationYear: null
                )
            ],
            Certificates: [],
            Projects: [
                new FastApiProjectDto(
                    Name: "",
                    Description: "Project with empty name",
                    Technologies: []
                )
            ],
            Technologies: []
        );

        // Act
        var structuredDto = FastApiCvMapper.ToStructuredCvDataDto(fastApiCv);

        // Assert:
        // 1. Company was null -> maps to empty string, NOT "Company"
        Assert.Single(structuredDto.Experiences);
        Assert.Equal(string.Empty, structuredDto.Experiences[0].CompanyName);
        Assert.NotEqual("Company", structuredDto.Experiences[0].CompanyName);

        // 2. Institution was null -> maps to empty string, NOT "University"
        Assert.Single(structuredDto.Educations);
        Assert.Equal(string.Empty, structuredDto.Educations[0].School);
        Assert.NotEqual("University", structuredDto.Educations[0].School);

        // 3. Project had empty name -> omitted, NOT named "Project"
        Assert.Empty(structuredDto.Projects);
    }
}
