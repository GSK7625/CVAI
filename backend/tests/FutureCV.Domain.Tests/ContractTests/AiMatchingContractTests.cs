using System.Text.Json;
using FutureCV.Application.Features.AiMatching.DTOs;
using Xunit;

namespace FutureCV.Domain.Tests.ContractTests;

public class AiMatchingContractTests
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    private static string GetScenarioPath(string fileName)
    {
        // Search relative to test output or source tree
        var baseDir = AppDomain.CurrentDomain.BaseDirectory;
        var relativeCandidates = new[]
        {
            Path.Combine(baseDir, "..", "..", "..", "..", "..", "backend-ai", "tests", "fixtures", "contracts", "scenarios", fileName),
            Path.Combine(baseDir, "..", "..", "..", "..", "backend-ai", "tests", "fixtures", "contracts", "scenarios", fileName),
            Path.GetFullPath(Path.Combine(baseDir, "../../../../../backend-ai/tests/fixtures/contracts/scenarios", fileName))
        };

        foreach (var path in relativeCandidates)
        {
            if (File.Exists(path)) return Path.GetFullPath(path);
        }

        // Direct fallback
        var direct = Path.GetFullPath(@"D:\My Project\CDTH\FutureCV\backend-ai\tests\fixtures\contracts\scenarios\" + fileName);
        if (File.Exists(direct)) return direct;

        throw new FileNotFoundException($"Scenario fixture not found: {fileName}");
    }

    private static string LoadScenarioJson(string fileName)
    {
        var path = GetScenarioPath(fileName);
        return File.ReadAllText(path);
    }

    [Fact]
    public void Scenario01_FullValidCvAndJob_RoundTripsAccurately()
    {
        var json = LoadScenarioJson("01_full_valid_cv_and_job.json");
        var req = JsonSerializer.Deserialize<AiMatchRequest>(json, JsonOptions);

        Assert.NotNull(req);
        Assert.NotNull(req.Cv);
        Assert.NotNull(req.Job);
        Assert.Equal("Nguyễn Văn An", req.Cv.FullName);
        Assert.Contains("C#", req.Cv.Skills);
        Assert.Single(req.Cv.WorkExperience);
        Assert.Equal("Backend Developer", req.Cv.WorkExperience[0].JobTitle);
        Assert.Single(req.Cv.Education);
        Assert.Equal("Kỹ sư", req.Cv.Education[0].Degree);
        Assert.Single(req.Cv.Projects);
        Assert.Equal("Senior .NET Backend Engineer", req.Job.Title);
        Assert.Equal(2.0, req.Job.MinimumExperienceYears);
        Assert.Contains("C#", req.Job.RequiredSkills);
        Assert.Contains("Docker", req.Job.PreferredSkills);

        // Serialize back and verify
        var serialized = JsonSerializer.Serialize(req, JsonOptions);
        var roundTrip = JsonSerializer.Deserialize<AiMatchRequest>(serialized, JsonOptions);
        Assert.NotNull(roundTrip);
        Assert.Equal(req.Cv.FullName, roundTrip.Cv.FullName);
        Assert.Equal(req.Job.Title, roundTrip.Job.Title);
    }

    [Fact]
    public void Scenario02_FresherNoExperience_DeserializesCleanly()
    {
        var json = LoadScenarioJson("02_fresher_no_experience.json");
        var req = JsonSerializer.Deserialize<AiMatchRequest>(json, JsonOptions);

        Assert.NotNull(req);
        Assert.Empty(req.Cv.WorkExperience);
        Assert.Equal("Trần Thị Bình", req.Cv.FullName);
        Assert.Equal(0.0, req.Job.MinimumExperienceYears);
    }

    [Fact]
    public void Scenario03_MissingOptionalEducation_DeserializesCleanly()
    {
        var json = LoadScenarioJson("03_missing_optional_education.json");
        var req = JsonSerializer.Deserialize<AiMatchRequest>(json, JsonOptions);

        Assert.NotNull(req);
        Assert.Empty(req.Cv.Education);
        Assert.Null(req.Job.EducationRequirement);
        Assert.Single(req.Cv.WorkExperience);
        Assert.Equal(5.0, req.Cv.WorkExperience[0].YearsOfExperience);
    }

    [Fact]
    public void Scenario04_EmptyPreferredSkills_DeserializesCleanly()
    {
        var json = LoadScenarioJson("04_empty_preferred_skills.json");
        var req = JsonSerializer.Deserialize<AiMatchRequest>(json, JsonOptions);

        Assert.NotNull(req);
        Assert.Empty(req.Job.PreferredSkills);
        Assert.Equal(3, req.Job.RequiredSkills.Count);
    }

    [Fact]
    public void Scenario05_DuplicateSkills_DeserializesCleanly()
    {
        var json = LoadScenarioJson("05_duplicate_skills.json");
        var req = JsonSerializer.Deserialize<AiMatchRequest>(json, JsonOptions);

        Assert.NotNull(req);
        Assert.NotEmpty(req.Cv.Skills);
        Assert.NotEmpty(req.Job.RequiredSkills);
    }

    [Fact]
    public void Scenario06_UnknownDegree_DeserializesCleanly()
    {
        var json = LoadScenarioJson("06_unknown_degree.json");
        var req = JsonSerializer.Deserialize<AiMatchRequest>(json, JsonOptions);

        Assert.NotNull(req);
        Assert.Equal("Bootcamp Intensive Certificate", req.Cv.Education[0].Degree);
        Assert.Equal("Chứng chỉ nghề hoặc tương đương", req.Job.EducationRequirement);
    }

    [Fact]
    public void Scenario07_MultipleExperienceEntries_DeserializesCleanly()
    {
        var json = LoadScenarioJson("07_multiple_experience_entries.json");
        var req = JsonSerializer.Deserialize<AiMatchRequest>(json, JsonOptions);

        Assert.NotNull(req);
        Assert.Equal(3, req.Cv.WorkExperience.Count);
        Assert.Equal("MoMo", req.Cv.WorkExperience[0].Company);
        Assert.Equal("ZaloPay", req.Cv.WorkExperience[1].Company);
        Assert.Equal("TMA Solutions", req.Cv.WorkExperience[2].Company);
        Assert.Equal(2, req.Cv.Education.Count);
    }

    [Fact]
    public void Scenario08_ProjectsAbsent_DeserializesCleanly()
    {
        var json = LoadScenarioJson("08_projects_absent.json");
        var req = JsonSerializer.Deserialize<AiMatchRequest>(json, JsonOptions);

        Assert.NotNull(req);
        Assert.Empty(req.Cv.Projects);
        Assert.Equal("Bùi Văn Long", req.Cv.FullName);
    }

    [Fact]
    public void Scenario09_UnicodeVietnameseContent_PreservesEncoding()
    {
        var json = LoadScenarioJson("09_unicode_vietnamese_content.json");
        var req = JsonSerializer.Deserialize<AiMatchRequest>(json, JsonOptions);

        Assert.NotNull(req);
        Assert.Equal("Ngô Hoàng Trọng Nghĩa", req.Cv.FullName);
        Assert.Contains("Xử lý ngôn ngữ tự nhiên", req.Cv.Skills);
        Assert.Contains("VinBigdata", req.Cv.WorkExperience[0].Company);
        Assert.Equal("Chuyên viên Cao cấp Trí tuệ Nhân tạo (NLP / LLM)", req.Job.Title);
        Assert.Equal("Thành phố Hà Nội", req.Job.Location);
    }

    [Fact]
    public void Scenario10_InvalidMatchScorePayload_DetectsInvalidBounds()
    {
        var json = LoadScenarioJson("10_invalid_match_score_payload.json");
        var res = JsonSerializer.Deserialize<AiMatchResultDto>(json, JsonOptions);

        Assert.NotNull(res);
        // Validates score bounds: score must be between 0 and 100
        Assert.False(res.MatchScore is >= 0 and <= 100, "Score 150 must be identified as outside the valid [0, 100] range");
    }

    [Fact]
    public void Scenario11_ResponseWithLlmFallbackMeta_DeserializesCleanly()
    {
        var json = LoadScenarioJson("11_response_llm_fallback_meta.json");
        var res = JsonSerializer.Deserialize<AiMatchResultDto>(json, JsonOptions);

        Assert.NotNull(res);
        Assert.Equal(82, res.MatchScore);
        Assert.Equal("match-result-v1", res.Meta.ContractVersion);
        Assert.Equal("deterministic-fallback", res.Meta.ExplanationMode);
        Assert.True(res.Meta.LlmInvoked);
        Assert.Contains("Điểm phù hợp: 82/100", res.MatchExplanation);
    }

    [Fact]
    public void CanonicalFixture_WithExplanation_DeserializesAccurately()
    {
        var baseDir = AppDomain.CurrentDomain.BaseDirectory;
        var direct = Path.GetFullPath(@"D:\My Project\CDTH\FutureCV\backend-ai\tests\fixtures\contracts\match_result_v1_with_explanation.json");
        var json = File.ReadAllText(direct);
        var res = JsonSerializer.Deserialize<AiMatchResultDto>(json, JsonOptions);

        Assert.NotNull(res);
        Assert.Equal(88, res.MatchScore);
        Assert.Equal(3, res.MatchedSkills.Count);
        Assert.Single(res.MissingSkills);
        Assert.Equal("match-result-v1", res.Meta.ContractVersion);
        Assert.True(res.Meta.LlmInvoked);
        Assert.Equal("llm", res.Meta.ExplanationMode);
    }

    [Fact]
    public void CanonicalFixture_NoExplanation_DeserializesAccurately()
    {
        var direct = Path.GetFullPath(@"D:\My Project\CDTH\FutureCV\backend-ai\tests\fixtures\contracts\match_result_v1_no_explanation.json");
        var json = File.ReadAllText(direct);
        var res = JsonSerializer.Deserialize<AiMatchResultDto>(json, JsonOptions);

        Assert.NotNull(res);
        Assert.Equal(88, res.MatchScore);
        Assert.Equal("match-result-v1", res.Meta.ContractVersion);
        Assert.False(res.Meta.LlmInvoked);
        Assert.Equal("deterministic", res.Meta.ExplanationMode);
    }
}
