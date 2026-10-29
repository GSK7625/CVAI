using System.Text.Json;
using FutureCV.Application.Features.AiMatching.DTOs;
using Xunit;

namespace FutureCV.Domain.Tests.ContractTests;

public class AiMatchingSerializationTests
{
    private static readonly JsonSerializerOptions StrictJsonOptions = new()
    {
        PropertyNameCaseInsensitive = false // Strict casing check
    };

    private static readonly JsonSerializerOptions PermissiveJsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    private static string GetFixturePath(string relativePath)
    {
        // 1. Check output directory copied via MSBuild LinkBase
        var outputDir = Path.Combine(AppContext.BaseDirectory, "Fixtures", "Contracts", relativePath);
        if (File.Exists(outputDir))
        {
            return outputDir;
        }

        // 2. Fallback: navigate up to repo root
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            var candidate = Path.Combine(dir.FullName, "backend-ai", "tests", "fixtures", "contracts", relativePath);
            if (File.Exists(candidate))
            {
                return candidate;
            }
            dir = dir.Parent;
        }

        throw new FileNotFoundException($"Shared contract fixture '{relativePath}' could not be located.");
    }

    // =========================================================================
    // 1. MatchRequest Serialization — Actual Schema vs Drifted Keys
    // =========================================================================

    [Fact]
    public void AiMatchRequest_SerializesToExactSnakeCase_WithAllAuthoritativePythonKeys()
    {
        var request = new AiMatchRequest(
            Cv: new AiStructuredCvDto(
                FullName: "Nguyen Van A",
                Email: "a@example.com",
                Phone: "0901234567",
                CareerSummary: "Senior Backend Developer",
                Skills: ["C#", ".NET", "PostgreSQL"],
                WorkExperience: [
                    new AiWorkExperienceDto(
                        JobTitle: "Lead Engineer",
                        Company: "Tech Corp",
                        Duration: "2 years",
                        StartDate: "2022-01-01",
                        EndDate: "2024-01-01",
                        YearsOfExperience: 2.0,
                        Description: "System architecture"
                    )
                ],
                Education: [
                    new AiEducationDto(
                        Degree: "Bachelor of Science",
                        Institution: "Polytechnic",
                        FieldOfStudy: "Computer Science",
                        GraduationYear: "2021"
                    )
                ],
                Certificates: ["AWS Certified"],
                Projects: [
                    new AiProjectDto(
                        Name: "E-Commerce",
                        Description: "Payment Gateway",
                        Technologies: ["C#", "Redis"]
                    )
                ],
                Technologies: ["C#", "Redis"]
            ),
            Job: new AiStructuredJobDto(
                Title: "Principal Engineer",
                Description: "Lead engineering org",
                RequiredSkills: ["C#", ".NET"],
                PreferredSkills: ["Kubernetes"],
                MinimumExperienceYears: 5.0,
                EducationRequirement: "Bachelor",
                Location: "Hanoi",
                Salary: "3000 - 5000 USD",
                EmploymentType: "Full-time"
            )
        );

        var json = JsonSerializer.Serialize(request, StrictJsonOptions);

        // Assert exact authoritative CV snake_case field names are present
        Assert.Contains("\"cv\"", json);
        Assert.Contains("\"full_name\"", json);
        Assert.Contains("\"email\"", json);
        Assert.Contains("\"phone\"", json);
        Assert.Contains("\"career_summary\"", json);
        Assert.Contains("\"skills\"", json);
        Assert.Contains("\"work_experience\"", json);
        Assert.Contains("\"job_title\"", json);
        Assert.Contains("\"company\"", json);
        Assert.Contains("\"duration\"", json);
        Assert.Contains("\"start_date\"", json);
        Assert.Contains("\"end_date\"", json);
        Assert.Contains("\"years_of_experience\"", json);
        Assert.Contains("\"education\"", json);
        Assert.Contains("\"degree\"", json);
        Assert.Contains("\"institution\"", json);
        Assert.Contains("\"field_of_study\"", json);
        Assert.Contains("\"graduation_year\"", json);
        Assert.Contains("\"certificates\"", json);
        Assert.Contains("\"projects\"", json);
        Assert.Contains("\"technologies\"", json);

        // Assert exact authoritative Job snake_case field names are present
        Assert.Contains("\"job\"", json);
        Assert.Contains("\"title\"", json);
        Assert.Contains("\"description\"", json);
        Assert.Contains("\"required_skills\"", json);
        Assert.Contains("\"preferred_skills\"", json);
        Assert.Contains("\"minimum_experience_years\"", json);
        Assert.Contains("\"education_requirement\"", json);
        Assert.Contains("\"location\"", json);
        Assert.Contains("\"salary\"", json);
        Assert.Contains("\"employment_type\"", json);
    }

    [Fact]
    public void AiMatchRequest_Serialization_ExplicitlyExcludesAllDriftedFields()
    {
        var request = new AiMatchRequest(
            Cv: new AiStructuredCvDto(
                FullName: "Nguyen Van A",
                Email: "a@example.com",
                Phone: "0901234567",
                CareerSummary: "Senior Backend Developer",
                Skills: ["C#"],
                WorkExperience: [
                    new AiWorkExperienceDto(
                        JobTitle: "Lead Engineer",
                        Company: "Tech Corp",
                        Duration: "2 years",
                        StartDate: "2022-01-01",
                        EndDate: "2024-01-01",
                        YearsOfExperience: 2.0,
                        Description: "System architecture"
                    )
                ],
                Education: [
                    new AiEducationDto(
                        Degree: "Bachelor",
                        Institution: "Polytechnic",
                        FieldOfStudy: "IT",
                        GraduationYear: "2021"
                    )
                ],
                Certificates: [],
                Projects: [],
                Technologies: []
            ),
            Job: new AiStructuredJobDto(
                Title: "Principal Engineer",
                Description: "Lead engineering org",
                RequiredSkills: ["C#"],
                PreferredSkills: [],
                MinimumExperienceYears: 5.0,
                EducationRequirement: null,
                Location: "Hanoi",
                Salary: "3000 USD",
                EmploymentType: "Full-time"
            )
        );

        var json = JsonSerializer.Serialize(request, StrictJsonOptions);

        // Assert drifted CV fields are NOT present
        Assert.DoesNotContain("\"personal_info\"", json);
        Assert.DoesNotContain("\"position\"", json);
        Assert.DoesNotContain("\"responsibilities\"", json);
        Assert.DoesNotContain("\"is_current\"", json);
        Assert.DoesNotContain("\"certifications\"", json);

        // Assert drifted Job fields are NOT present
        Assert.DoesNotContain("\"required_experience_years\"", json);
        Assert.DoesNotContain("\"department\"", json);
        Assert.DoesNotContain("\"salary_min\"", json);
        Assert.DoesNotContain("\"salary_max\"", json);
        Assert.DoesNotContain("\"currency\"", json);

        // Assert NO camelCase or PascalCase CLR leakage
        Assert.DoesNotContain("\"fullName\"", json);
        Assert.DoesNotContain("\"careerSummary\"", json);
        Assert.DoesNotContain("\"workExperience\"", json);
        Assert.DoesNotContain("\"jobTitle\"", json);
        Assert.DoesNotContain("\"yearsOfExperience\"", json);
        Assert.DoesNotContain("\"fieldOfStudy\"", json);
        Assert.DoesNotContain("\"graduationYear\"", json);
        Assert.DoesNotContain("\"requiredSkills\"", json);
        Assert.DoesNotContain("\"preferredSkills\"", json);
        Assert.DoesNotContain("\"minimumExperienceYears\"", json);
        Assert.DoesNotContain("\"educationRequirement\"", json);
        Assert.DoesNotContain("\"employmentType\"", json);
        Assert.DoesNotContain("\"FullName\"", json);
        Assert.DoesNotContain("\"CareerSummary\"", json);
        Assert.DoesNotContain("\"WorkExperience\"", json);
        Assert.DoesNotContain("\"JobTitle\"", json);
    }

    // =========================================================================
    // 2. MatchResult Serialization — Actual Schema vs Drifted Keys
    // =========================================================================

    [Fact]
    public void AiMatchResultDto_SerializesToExactSnakeCase_WithAllAuthoritativePythonKeys()
    {
        var dto = new AiMatchResultDto(
            MatchScore: 88,
            MatchedSkills: ["Python", "FastAPI", "PostgreSQL"],
            MissingSkills: ["Docker"],
            ExperienceComparison: "Yêu cầu: 2.0 năm. Ứng viên có: 3.5 năm.",
            EducationComparison: "Yêu cầu: Bachelor. Ứng viên có: Bachelor.",
            ProjectDomainRelevance: "Có 2/3 dự án phù hợp.",
            MatchExplanation: "Ứng viên có nền tảng vững chắc.",
            Meta: new AiResponseMetaDto(
                AlgorithmVersion: "matching-v0",
                AlgorithmVariant: "matching-v0",
                ContractVersion: "match-result-v1",
                SchemaVersion: "1.0.0",
                PromptVersion: "v1",
                Provider: "openai",
                Model: "gpt-4o-mini",
                EmbeddingProvider: null,
                EmbeddingModel: null,
                LlmInvoked: true,
                ExplanationMode: "llm",
                ProcessingTimeMs: 284.15,
                CorrelationId: "corr-fixture-with-exp"
            )
        );

        var json = JsonSerializer.Serialize(dto, StrictJsonOptions);

        // Assert top-level MatchResult authoritative keys
        Assert.Contains("\"match_score\"", json);
        Assert.Contains("\"matched_skills\"", json);
        Assert.Contains("\"missing_skills\"", json);
        Assert.Contains("\"experience_comparison\"", json);
        Assert.Contains("\"education_comparison\"", json);
        Assert.Contains("\"project_domain_relevance\"", json);
        Assert.Contains("\"match_explanation\"", json);
        Assert.Contains("\"meta\"", json);

        // Assert ResponseMeta authoritative keys
        Assert.Contains("\"algorithm_version\"", json);
        Assert.Contains("\"algorithm_variant\"", json);
        Assert.Contains("\"contract_version\"", json);
        Assert.Contains("\"schema_version\"", json);
        Assert.Contains("\"prompt_version\"", json);
        Assert.Contains("\"provider\"", json);
        Assert.Contains("\"model\"", json);
        Assert.Contains("\"llm_invoked\"", json);
        Assert.Contains("\"explanation_mode\"", json);
        Assert.Contains("\"processing_time_ms\"", json);
        Assert.Contains("\"correlation_id\"", json);
    }

    [Fact]
    public void AiMatchResultDto_Serialization_ExplicitlyExcludesAllDriftedFields()
    {
        var dto = new AiMatchResultDto(
            MatchScore: 75,
            MatchedSkills: ["C#"],
            MissingSkills: ["Docker"],
            ExperienceComparison: "Exp OK",
            EducationComparison: "Edu OK",
            ProjectDomainRelevance: "Proj OK",
            MatchExplanation: "Explanation OK",
            Meta: new AiResponseMetaDto(
                AlgorithmVersion: "1.0.0",
                ContractVersion: "match-result-v1",
                CorrelationId: "corr-test"
            )
        );

        var json = JsonSerializer.Serialize(dto, StrictJsonOptions);

        // Assert drifted response fields are NOT present
        Assert.DoesNotContain("\"score_breakdown\"", json);
        Assert.DoesNotContain("\"semantic_similarity\"", json);
        Assert.DoesNotContain("\"recommendation\"", json);
        Assert.DoesNotContain("\"strengths\"", json);
        Assert.DoesNotContain("\"weaknesses\"", json);
        Assert.DoesNotContain("\"actionable_feedback\"", json);
        Assert.DoesNotContain("\"red_flags\"", json);
        Assert.DoesNotContain("\"interview_questions\"", json);
        Assert.DoesNotContain("\"model_version\"", json);
        Assert.DoesNotContain("\"timestamp\"", json);
        Assert.DoesNotContain("\"latency_ms\"", json);
        Assert.DoesNotContain("\"processing_details\"", json);

        // Assert NO camelCase or PascalCase CLR leakage
        Assert.DoesNotContain("\"matchScore\"", json);
        Assert.DoesNotContain("\"matchedSkills\"", json);
        Assert.DoesNotContain("\"missingSkills\"", json);
        Assert.DoesNotContain("\"experienceComparison\"", json);
        Assert.DoesNotContain("\"educationComparison\"", json);
        Assert.DoesNotContain("\"projectDomainRelevance\"", json);
        Assert.DoesNotContain("\"matchExplanation\"", json);
        Assert.DoesNotContain("\"algorithmVersion\"", json);
        Assert.DoesNotContain("\"contractVersion\"", json);
        Assert.DoesNotContain("\"processingTimeMs\"", json);
        Assert.DoesNotContain("\"correlationId\"", json);
    }

    // =========================================================================
    // 3. True Cross-Contract Canonical Fixture Tests
    //    Validates that .NET accepts the identical JSON fixtures as Python
    // =========================================================================

    [Fact]
    public void CrossContract_Deserialize_MatchResult_WithExplanation_Fixture()
    {
        var fixturePath = GetFixturePath("match_result_v1_with_explanation.json");
        var json = File.ReadAllText(fixturePath);

        var result = JsonSerializer.Deserialize<AiMatchResultDto>(json, PermissiveJsonOptions);

        Assert.NotNull(result);
        Assert.Equal(88, result.MatchScore);
        Assert.Equal(["Python", "FastAPI", "PostgreSQL"], result.MatchedSkills);
        Assert.Equal(["Docker"], result.MissingSkills);
        Assert.Contains("2.0 năm", result.ExperienceComparison);
        Assert.Contains("Bachelor", result.EducationComparison);
        Assert.Contains("FastAPI", result.ProjectDomainRelevance);
        Assert.NotNull(result.MatchExplanation);
        Assert.Contains("Ứng viên có nền tảng vững chắc", result.MatchExplanation);

        Assert.NotNull(result.ExplanationDetails);
        Assert.Equal(3, result.ExplanationDetails.Strengths?.Count);
        Assert.Equal(1, result.ExplanationDetails.Gaps?.Count);
        Assert.Equal("Python", result.ExplanationDetails.Strengths?[0].Item);
        Assert.Equal("cv.skills", result.ExplanationDetails.Strengths?[0].EvidenceSource);
        Assert.Equal("Docker", result.ExplanationDetails.Gaps?[0].Requirement);

        Assert.NotNull(result.Meta);
        Assert.Equal("match-result-v1", result.Meta.ContractVersion);
        Assert.Equal("matching-v0", result.Meta.AlgorithmVersion);
        Assert.Equal("matching-v0", result.Meta.AlgorithmVariant);
        Assert.Equal("1.0.0", result.Meta.SchemaVersion);
        Assert.Equal("v1", result.Meta.PromptVersion);
        Assert.Equal("openai", result.Meta.Provider);
        Assert.Equal("gpt-4o-mini", result.Meta.Model);
        Assert.True(result.Meta.LlmInvoked);
        Assert.Equal("llm", result.Meta.ExplanationMode);
        Assert.Equal(284.15, result.Meta.ProcessingTimeMs);
        Assert.Equal("corr-fixture-with-exp", result.Meta.CorrelationId);
    }

    [Fact]
    public void CrossContract_Deserialize_MatchResult_NoExplanation_Fixture()
    {
        var fixturePath = GetFixturePath("match_result_v1_no_explanation.json");
        var json = File.ReadAllText(fixturePath);

        var result = JsonSerializer.Deserialize<AiMatchResultDto>(json, PermissiveJsonOptions);

        Assert.NotNull(result);
        Assert.Equal(88, result.MatchScore);
        Assert.Equal(["Python", "FastAPI", "PostgreSQL"], result.MatchedSkills);
        Assert.Equal(["Docker"], result.MissingSkills);
        Assert.NotNull(result.MatchExplanation);
        Assert.Contains("Điểm phù hợp:", result.MatchExplanation);

        Assert.NotNull(result.ExplanationDetails);
        Assert.Equal(3, result.ExplanationDetails.Strengths?.Count);

        Assert.NotNull(result.Meta);
        Assert.Equal("match-result-v1", result.Meta.ContractVersion);
        Assert.False(result.Meta.LlmInvoked);
        Assert.Equal("deterministic", result.Meta.ExplanationMode);
    }

    [Fact]
    public void CrossContract_Deserialize_MatchRequest_01_FullValidCvAndJob_Fixture()
    {
        var fixturePath = GetFixturePath(Path.Combine("scenarios", "01_full_valid_cv_and_job.json"));
        var json = File.ReadAllText(fixturePath);

        var request = JsonSerializer.Deserialize<AiMatchRequest>(json, PermissiveJsonOptions);

        Assert.NotNull(request);

        // Verify CV
        Assert.NotNull(request.Cv);
        Assert.Equal("Nguyễn Văn An", request.Cv.FullName);
        Assert.Equal("nguyen.an@example.com", request.Cv.Email);
        Assert.Equal("0912345678", request.Cv.Phone);
        Assert.Contains("Kỹ sư phần mềm 3 năm", request.Cv.CareerSummary);
        Assert.Equal(6, request.Cv.Skills.Count);
        Assert.Contains("FastAPI", request.Cv.Skills);

        Assert.Single(request.Cv.WorkExperience);
        var exp = request.Cv.WorkExperience[0];
        Assert.Equal("Backend Developer", exp.JobTitle);
        Assert.Equal("FPT Software", exp.Company);
        Assert.Equal("2022 - Hiện tại", exp.Duration);
        Assert.Equal("2022-01-01", exp.StartDate);
        Assert.Null(exp.EndDate);
        Assert.Equal(2.5, exp.YearsOfExperience);

        Assert.Single(request.Cv.Education);
        var edu = request.Cv.Education[0];
        Assert.Equal("Kỹ sư", edu.Degree);
        Assert.Equal("Đại học Bách Khoa TP.HCM", edu.Institution);
        Assert.Equal("Công nghệ thông tin", edu.FieldOfStudy);
        Assert.Equal("2022", edu.GraduationYear);

        Assert.Single(request.Cv.Certificates);
        Assert.Equal("AWS Certified Solutions Architect - Associate", request.Cv.Certificates[0]);

        Assert.Single(request.Cv.Projects);
        var proj = request.Cv.Projects[0];
        Assert.Equal("E-Commerce Microservices", proj.Name);
        Assert.Equal(4, proj.Technologies.Count);

        Assert.Equal(6, request.Cv.Technologies.Count);

        // Verify Job
        Assert.NotNull(request.Job);
        Assert.Equal("Senior .NET Backend Engineer", request.Job.Title);
        Assert.Contains("Tuyển dụng kỹ sư backend", request.Job.Description);
        Assert.Equal(3, request.Job.RequiredSkills.Count);
        Assert.Equal(2, request.Job.PreferredSkills.Count);
        Assert.Equal(2.0, request.Job.MinimumExperienceYears);
        Assert.Equal("Đại học / Cử nhân", request.Job.EducationRequirement);
        Assert.Equal("Hồ Chí Minh", request.Job.Location);
        Assert.Equal("25.000.000 - 35.000.000 VND", request.Job.Salary);
        Assert.Equal("Toàn thời gian", request.Job.EmploymentType);
    }

    [Fact]
    public void CrossContract_Deserialize_MatchRequest_02_FresherNoExperience_Fixture()
    {
        var fixturePath = GetFixturePath(Path.Combine("scenarios", "02_fresher_no_experience.json"));
        var json = File.ReadAllText(fixturePath);

        var request = JsonSerializer.Deserialize<AiMatchRequest>(json, PermissiveJsonOptions);

        Assert.NotNull(request);
        Assert.Equal("Trần Thị Bình", request.Cv.FullName);
        Assert.Empty(request.Cv.WorkExperience);
        Assert.Single(request.Cv.Education);
        Assert.Equal(0.0, request.Job.MinimumExperienceYears);
    }

    [Fact]
    public void CrossContract_Deserialize_MatchRequest_09_UnicodeVietnameseContent_Fixture()
    {
        var fixturePath = GetFixturePath(Path.Combine("scenarios", "09_unicode_vietnamese_content.json"));
        var json = File.ReadAllText(fixturePath);

        var request = JsonSerializer.Deserialize<AiMatchRequest>(json, PermissiveJsonOptions);

        Assert.NotNull(request);
        Assert.Equal("Ngô Hoàng Trọng Nghĩa", request.Cv.FullName);
        Assert.Contains("Xử lý ngôn ngữ tự nhiên", request.Cv.Skills);
        Assert.Equal("Kỹ sư Nghiên cứu AI", request.Cv.WorkExperience[0].JobTitle);
        Assert.Equal("Thạc sĩ Khoa học Máy tính", request.Cv.Education[0].Degree);
        Assert.Equal("Chuyên viên Cao cấp Trí tuệ Nhân tạo (NLP / LLM)", request.Job.Title);
        Assert.Equal("Thành phố Hà Nội", request.Job.Location);
    }

    [Fact]
    public void CrossContract_RoundTrip_SerializationPreservesContractInvariance()
    {
        var fixturePath = GetFixturePath(Path.Combine("scenarios", "01_full_valid_cv_and_job.json"));
        var originalJson = File.ReadAllText(fixturePath);

        var request1 = JsonSerializer.Deserialize<AiMatchRequest>(originalJson, PermissiveJsonOptions);
        Assert.NotNull(request1);

        // Serialize back
        var serializedJson = JsonSerializer.Serialize(request1, StrictJsonOptions);

        // Deserialize again
        var request2 = JsonSerializer.Deserialize<AiMatchRequest>(serializedJson, StrictJsonOptions);
        Assert.NotNull(request2);

        // Assert round-trip equivalence
        Assert.Equal(request1.Cv.FullName, request2.Cv.FullName);
        Assert.Equal(request1.Cv.Skills, request2.Cv.Skills);
        Assert.Equal(request1.Cv.WorkExperience.Count, request2.Cv.WorkExperience.Count);
        Assert.Equal(request1.Cv.WorkExperience[0].JobTitle, request2.Cv.WorkExperience[0].JobTitle);
        Assert.Equal(request1.Job.Title, request2.Job.Title);
        Assert.Equal(request1.Job.MinimumExperienceYears, request2.Job.MinimumExperienceYears);
        Assert.Equal(request1.Job.Salary, request2.Job.Salary);
    }
}
