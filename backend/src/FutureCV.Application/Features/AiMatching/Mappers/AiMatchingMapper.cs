using System.Globalization;
using FutureCV.Application.Features.AiMatching.DTOs;
using FutureCV.Application.Features.Candidate.DTOs;
using JobEntity = FutureCV.Domain.Entities.Job;

namespace FutureCV.Application.Features.AiMatching.Mappers;

/// <summary>
/// Domain-to-Contract mapper translating between FutureCV internal entities/DTOs
/// and external AI Matching contracts with strict semantic integrity.
/// CV mapping relies exclusively on selected CV data without fabricating evidence.
/// </summary>
public static class AiMatchingMapper
{
    public static AiStructuredCvDto ToAiStructuredCv(StructuredCvDataDto structuredCv)
    {
        ArgumentNullException.ThrowIfNull(structuredCv);

        var fullName = !string.IsNullOrWhiteSpace(structuredCv.FullName)
            ? structuredCv.FullName.Trim()
            : null;

        var email = !string.IsNullOrWhiteSpace(structuredCv.Email)
            ? structuredCv.Email.Trim()
            : null;

        var phone = !string.IsNullOrWhiteSpace(structuredCv.Phone)
            ? structuredCv.Phone.Trim()
            : null;

        var summary = !string.IsNullOrWhiteSpace(structuredCv.Summary)
            ? structuredCv.Summary.Trim()
            : null;

        // Skills resolution: parsed CV skills only
        var skills = structuredCv.Skills != null && structuredCv.Skills.Count > 0
            ? structuredCv.Skills
                .Where(s => !string.IsNullOrWhiteSpace(s))
                .Select(s => s.Trim())
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToList()
            : new List<string>();

        // Work experience resolution: no fabricated job titles
        var workExperiences = new List<AiWorkExperienceDto>();
        if (structuredCv.Experiences != null && structuredCv.Experiences.Count > 0)
        {
            foreach (var exp in structuredCv.Experiences)
            {
                var title = !string.IsNullOrWhiteSpace(exp.Position) ? exp.Position.Trim() : null;
                var company = exp.CompanyName?.Trim() ?? string.Empty;
                var startDate = exp.StartDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
                var endDate = exp.IsCurrent ? null : exp.EndDate?.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

                double years = 0.0;
                if (exp.EndDate.HasValue)
                {
                    years = Math.Max(0.0, Math.Min(60.0, (exp.EndDate.Value.ToDateTime(TimeOnly.MinValue) - exp.StartDate.ToDateTime(TimeOnly.MinValue)).TotalDays / 365.25));
                }
                else if (exp.IsCurrent)
                {
                    years = Math.Max(0.0, Math.Min(60.0, (DateTime.UtcNow - exp.StartDate.ToDateTime(TimeOnly.MinValue)).TotalDays / 365.25));
                }

                workExperiences.Add(new AiWorkExperienceDto(
                    JobTitle: title,
                    Company: company,
                    Duration: string.Empty,
                    StartDate: startDate,
                    EndDate: endDate,
                    YearsOfExperience: Math.Round(years, 1),
                    Description: exp.Description?.Trim() ?? string.Empty
                ));
            }
        }

        // Education resolution: no fabricated degrees
        var educations = new List<AiEducationDto>();
        if (structuredCv.Educations != null && structuredCv.Educations.Count > 0)
        {
            foreach (var edu in structuredCv.Educations)
            {
                var degree = !string.IsNullOrWhiteSpace(edu.Degree)
                    ? edu.Degree.Trim()
                    : (!string.IsNullOrWhiteSpace(edu.Major) ? edu.Major.Trim() : null);

                educations.Add(new AiEducationDto(
                    Degree: degree,
                    Institution: edu.School?.Trim() ?? string.Empty,
                    FieldOfStudy: edu.Major?.Trim() ?? string.Empty,
                    GraduationYear: edu.EndYear?.ToString(CultureInfo.InvariantCulture)
                ));
            }
        }

        // Certificates resolution: strictly empty for selected CV data (never fabricate or fallback)
        var certificates = new List<string>();

        // Projects resolution: skip unnamed projects rather than inventing placeholder names
        var projects = new List<AiProjectDto>();
        var technologies = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        if (structuredCv.Projects != null && structuredCv.Projects.Count > 0)
        {
            foreach (var proj in structuredCv.Projects)
            {
                if (string.IsNullOrWhiteSpace(proj.Name))
                {
                    continue;
                }

                var pTechs = ParseTechnologies(proj.Technologies);
                foreach (var t in pTechs) technologies.Add(t);

                projects.Add(new AiProjectDto(
                    Name: proj.Name.Trim(),
                    Description: proj.Description?.Trim() ?? string.Empty,
                    Technologies: pTechs
                ));
            }
        }

        return new AiStructuredCvDto(
            FullName: fullName,
            Email: email,
            Phone: phone,
            CareerSummary: summary,
            Skills: skills,
            WorkExperience: workExperiences,
            Education: educations,
            Certificates: certificates,
            Projects: projects,
            Technologies: technologies.ToList()
        );
    }

    public static AiStructuredJobDto ToAiStructuredJob(JobEntity job)
    {
        ArgumentNullException.ThrowIfNull(job);

        var title = !string.IsNullOrWhiteSpace(job.Title) ? job.Title.Trim() : "Vị trí tuyển dụng";
        var description = job.Description?.Trim() ?? string.Empty;

        if (!string.IsNullOrWhiteSpace(job.Requirements))
        {
            description = string.IsNullOrWhiteSpace(description)
                ? job.Requirements.Trim()
                : $"{description}\n\nYêu cầu công việc:\n{job.Requirements.Trim()}";
        }

        var requiredSkills = job.JobSkills != null
            ? job.JobSkills
                .Where(js => js.IsRequired && js.Skill != null && !string.IsNullOrWhiteSpace(js.Skill.Name))
                .Select(js => js.Skill.Name.Trim())
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToList()
            : new List<string>();

        var preferredSkills = job.JobSkills != null
            ? job.JobSkills
                .Where(js => !js.IsRequired && js.Skill != null && !string.IsNullOrWhiteSpace(js.Skill.Name))
                .Select(js => js.Skill.Name.Trim())
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToList()
            : new List<string>();

        double? minExp = job.ExperienceYearsMin.HasValue
            ? Math.Max(0.0, Math.Min(60.0, (double)job.ExperienceYearsMin.Value))
            : null;

        string? salary = null;
        if (job.SalaryMin.HasValue || job.SalaryMax.HasValue)
        {
            var minStr = job.SalaryMin?.ToString(CultureInfo.InvariantCulture);
            var maxStr = job.SalaryMax?.ToString(CultureInfo.InvariantCulture);
            salary = $"{minStr} - {maxStr} {job.SalaryCurrency}".Trim();
        }

        return new AiStructuredJobDto(
            Title: title,
            Description: description,
            RequiredSkills: requiredSkills,
            PreferredSkills: preferredSkills,
            MinimumExperienceYears: minExp,
            EducationRequirement: null, // Level is seniority, not degree; Job entity has no degree column
            Location: job.Location?.Name?.Trim(),
            Salary: salary,
            EmploymentType: job.EmploymentType?.Name?.Trim()
        );
    }

    public static AiMatchRequest ToAiMatchRequest(StructuredCvDataDto structuredCv, JobEntity job)
    {
        ArgumentNullException.ThrowIfNull(structuredCv);
        ArgumentNullException.ThrowIfNull(job);

        return new AiMatchRequest(
            Cv: ToAiStructuredCv(structuredCv),
            Job: ToAiStructuredJob(job)
        );
    }

    private static List<string> ParseTechnologies(string? techString)
    {
        if (string.IsNullOrWhiteSpace(techString))
            return [];

        return techString
            .Split(new[] { ',', ';', '|' }, StringSplitOptions.RemoveEmptyEntries)
            .Select(t => t.Trim())
            .Where(t => !string.IsNullOrEmpty(t))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();
    }
}
