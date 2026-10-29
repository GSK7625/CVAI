using FutureCV.Application.Features.AiMatching.Mappers;
using FutureCV.Application.Features.Candidate.DTOs;
using FutureCV.Domain.Entities;
using Xunit;

namespace FutureCV.Domain.Tests.ContractTests;

public class AiMatchingMapperTests
{
    [Fact]
    public void ToAiStructuredCv_WithValidStructuredData_MapsAccurately()
    {
        var structuredCv = new StructuredCvDataDto(
            FullName: "Nguyễn Văn Structured",
            Email: "test@futurecv.com",
            Phone: "0999888777",
            Summary: "Parsed summary",
            Skills: ["C#", ".NET", "PostgreSQL"],
            Experiences: [
                new CvExperienceDto(
                    CompanyName: "FutureTech",
                    Position: "Software Engineer",
                    StartDate: new DateOnly(2022, 1, 1),
                    EndDate: new DateOnly(2024, 1, 1),
                    IsCurrent: false,
                    Description: "Backend dev"
                )
            ],
            Educations: [
                new CvEducationDto(
                    School: "Đại học Bách Khoa",
                    Degree: "Kỹ sư",
                    Major: "CNTT",
                    StartYear: 2017,
                    EndYear: 2022,
                    Description: "Tốt nghiệp loại giỏi"
                )
            ],
            Projects: [
                new CvProjectDto(
                    Name: "AI Project",
                    Role: "Lead",
                    StartDate: null,
                    EndDate: null,
                    IsCurrent: false,
                    Description: "NLP platform",
                    Technologies: "Python, FastAPI, PyTorch"
                )
            ]
        );

        var result = AiMatchingMapper.ToAiStructuredCv(structuredCv);

        Assert.Equal("Nguyễn Văn Structured", result.FullName);
        Assert.Equal("test@futurecv.com", result.Email);
        Assert.Equal("0999888777", result.Phone);
        Assert.Equal("Parsed summary", result.CareerSummary);
        Assert.Equal(3, result.Skills.Count);
        Assert.Single(result.WorkExperience);
        Assert.Equal("Software Engineer", result.WorkExperience[0].JobTitle);
        Assert.Equal(2.0, result.WorkExperience[0].YearsOfExperience);
        Assert.Single(result.Education);
        Assert.Equal("Kỹ sư", result.Education[0].Degree);
        Assert.Single(result.Projects);
        Assert.Equal(3, result.Projects[0].Technologies.Count);
        Assert.Contains("PyTorch", result.Technologies);
    }

    [Fact]
    public void ToAiStructuredCv_WithNullOptionalFields_DoesNotFabricateQualifications()
    {
        var structuredCv = new StructuredCvDataDto(
            FullName: "",
            Email: null,
            Phone: null,
            Summary: null,
            Skills: [],
            Experiences: [
                new CvExperienceDto(
                    CompanyName: "Company X",
                    Position: null, // Null position
                    StartDate: new DateOnly(2023, 1, 1),
                    EndDate: null,
                    IsCurrent: true,
                    Description: null
                )
            ],
            Educations: [
                new CvEducationDto(
                    School: "University Y",
                    Degree: null, // Null degree
                    Major: null,
                    StartYear: null,
                    EndYear: null,
                    Description: null
                )
            ],
            Projects: []
        );

        var result = AiMatchingMapper.ToAiStructuredCv(structuredCv);

        Assert.Null(result.FullName);
        Assert.Null(result.CareerSummary);
        Assert.Single(result.WorkExperience);
        Assert.Null(result.WorkExperience[0].JobTitle); // No fabricated "Chuyên viên"
        Assert.Single(result.Education);
        Assert.Null(result.Education[0].Degree); // No fabricated "Đại học"
        Assert.Empty(result.Certificates);
        Assert.Empty(result.Projects);
    }

    [Fact]
    public void ToAiStructuredCv_WithUnnamedProject_SkipsProjectRecord()
    {
        var structuredCv = new StructuredCvDataDto(
            FullName: "Lê Minh Project",
            Email: "le.minh@example.com",
            Phone: null,
            Summary: null,
            Skills: ["Java"],
            Experiences: [],
            Educations: [],
            Projects: [
                new CvProjectDto(
                    Name: "   ", // Empty name
                    Role: "Developer",
                    StartDate: null,
                    EndDate: null,
                    IsCurrent: false,
                    Description: "Unnamed project without evidence",
                    Technologies: "Spring Boot"
                ),
                new CvProjectDto(
                    Name: "Named System",
                    Role: "Developer",
                    StartDate: null,
                    EndDate: null,
                    IsCurrent: false,
                    Description: "Valid project",
                    Technologies: "Java"
                )
            ]
        );

        var result = AiMatchingMapper.ToAiStructuredCv(structuredCv);

        Assert.Single(result.Projects); // Empty name skipped, no fabricated "Dự án"
        Assert.Equal("Named System", result.Projects[0].Name);
    }

    [Fact]
    public void ToAiStructuredJob_SetsEducationRequirementToNull()
    {
        var seniorityLevel = new JobLevel { Name = "Senior" };

        var job = new Job
        {
            Id = Guid.NewGuid(),
            Title = "Senior Backend Engineer",
            Description = "Lead backend systems.",
            Level = seniorityLevel, // Seniority, not education
            JobSkills = []
        };

        var result = AiMatchingMapper.ToAiStructuredJob(job);

        Assert.Equal("Senior Backend Engineer", result.Title);
        Assert.Null(result.EducationRequirement); // Seniority must NOT be mapped to education_requirement
    }

    [Fact]
    public void ToAiStructuredJob_WithJobSkills_SeparatesRequiredAndPreferred()
    {
        var skillCSharp = new Skill { Name = "C#" };
        var skillDocker = new Skill { Name = "Docker" };

        var job = new Job
        {
            Id = Guid.NewGuid(),
            Title = "Backend Tech Lead",
            Description = "Lead backend systems.",
            Requirements = "5+ years experience.",
            ExperienceYearsMin = 5,
            SalaryMin = 40000000,
            SalaryMax = 60000000,
            SalaryCurrency = "VND",
            JobSkills = [
                new JobSkill { Skill = skillCSharp, IsRequired = true },
                new JobSkill { Skill = skillDocker, IsRequired = false }
            ]
        };

        var result = AiMatchingMapper.ToAiStructuredJob(job);

        Assert.Equal("Backend Tech Lead", result.Title);
        Assert.Contains("5+ years experience", result.Description);
        Assert.Contains("C#", result.RequiredSkills);
        Assert.DoesNotContain("Docker", result.RequiredSkills);
        Assert.Contains("Docker", result.PreferredSkills);
        Assert.Equal(5.0, result.MinimumExperienceYears);
        Assert.Equal("40000000 - 60000000 VND", result.Salary);
        Assert.Null(result.EducationRequirement);
    }

    [Fact]
    public void ToAiStructuredCv_NullStructuredCv_Throws()
    {
        Assert.Throws<ArgumentNullException>(() => AiMatchingMapper.ToAiStructuredCv(null!));
    }

    [Fact]
    public void ToAiMatchRequest_NullArguments_Throws()
    {
        var job = new Job { Title = "Test Job" };
        var structuredCv = new StructuredCvDataDto(
            FullName: "Test",
            Email: null,
            Phone: null,
            Summary: null,
            Skills: [],
            Experiences: [],
            Educations: [],
            Projects: []
        );

        Assert.Throws<ArgumentNullException>(() => AiMatchingMapper.ToAiMatchRequest(null!, job));
        Assert.Throws<ArgumentNullException>(() => AiMatchingMapper.ToAiMatchRequest(structuredCv, null!));
    }
}
