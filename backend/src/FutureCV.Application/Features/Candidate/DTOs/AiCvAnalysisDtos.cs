using System.Text.Json.Serialization;

namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record FastApiWorkExperienceDto(
    [property: JsonPropertyName("job_title")] string? JobTitle,
    [property: JsonPropertyName("company")] string? Company,
    [property: JsonPropertyName("duration")] string? Duration,
    [property: JsonPropertyName("start_date")] string? StartDate,
    [property: JsonPropertyName("end_date")] string? EndDate,
    [property: JsonPropertyName("years_of_experience")] double? YearsOfExperience,
    [property: JsonPropertyName("description")] string? Description);

public sealed record FastApiEducationDto(
    [property: JsonPropertyName("degree")] string? Degree,
    [property: JsonPropertyName("institution")] string? Institution,
    [property: JsonPropertyName("field_of_study")] string? FieldOfStudy,
    [property: JsonPropertyName("graduation_year")] string? GraduationYear);

public sealed record FastApiProjectDto(
    [property: JsonPropertyName("name")] string? Name,
    [property: JsonPropertyName("description")] string? Description,
    [property: JsonPropertyName("technologies")] List<string>? Technologies);

public sealed record FastApiStructuredCvDto(
    [property: JsonPropertyName("full_name")] string? FullName,
    [property: JsonPropertyName("email")] string? Email,
    [property: JsonPropertyName("phone")] string? Phone,
    [property: JsonPropertyName("career_summary")] string? CareerSummary,
    [property: JsonPropertyName("skills")] List<string>? Skills,
    [property: JsonPropertyName("work_experience")] List<FastApiWorkExperienceDto>? WorkExperience,
    [property: JsonPropertyName("education")] List<FastApiEducationDto>? Education,
    [property: JsonPropertyName("certificates")] List<string>? Certificates,
    [property: JsonPropertyName("projects")] List<FastApiProjectDto>? Projects,
    [property: JsonPropertyName("technologies")] List<string>? Technologies);

public sealed record FastApiCvAnalysisResponseDto(
    [property: JsonPropertyName("structured_cv")] FastApiStructuredCvDto? StructuredCv,
    [property: JsonPropertyName("cv_score")] int CvScore,
    [property: JsonPropertyName("strengths")] List<string>? Strengths,
    [property: JsonPropertyName("weaknesses")] List<string>? Weaknesses,
    [property: JsonPropertyName("improvement_suggestions")] List<string>? ImprovementSuggestions,
    [property: JsonPropertyName("raw_text")] string? RawText);

public static class FastApiCvMapper
{
    public static StructuredCvDataDto ToStructuredCvDataDto(FastApiStructuredCvDto? source)
    {
        if (source is null)
        {
            return new StructuredCvDataDto(
                string.Empty,
                null,
                null,
                null,
                [],
                [],
                [],
                []
            );
        }

        // 1. Skills extraction & deduplication preserving case
        var combinedSkills = new List<string>();
        var seenSkills = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        if (source.Skills != null)
        {
            foreach (var s in source.Skills)
            {
                var trimmed = s?.Trim();
                if (!string.IsNullOrEmpty(trimmed) && seenSkills.Add(trimmed))
                {
                    combinedSkills.Add(trimmed);
                }
            }
        }

        if (source.Technologies != null)
        {
            foreach (var s in source.Technologies)
            {
                var trimmed = s?.Trim();
                if (!string.IsNullOrEmpty(trimmed) && seenSkills.Add(trimmed))
                {
                    combinedSkills.Add(trimmed);
                }
            }
        }

        // 2. Work Experiences
        var experiences = new List<CvExperienceDto>();
        if (source.WorkExperience != null)
        {
            foreach (var exp in source.WorkExperience)
            {
                var parsedStartDate = ParseDateOnly(exp.StartDate);
                if (!parsedStartDate.HasValue)
                {
                    // AI-DEMO-004: CvExperienceDto.StartDate hiện không nullable.
                    // Bỏ qua experience chưa có ngày bắt đầu, không tự thêm hai năm kinh nghiệm.
                    continue;
                }

                // AI-DEMO-004: Không tự kết luận đang làm hiện tại nếu không có từ khóa rõ ràng
                var isCurrent = (!string.IsNullOrWhiteSpace(exp.EndDate) && (
                                    exp.EndDate.Contains("present", StringComparison.OrdinalIgnoreCase) ||
                                    exp.EndDate.Contains("hiện tại", StringComparison.OrdinalIgnoreCase) ||
                                    exp.EndDate.Contains("nay", StringComparison.OrdinalIgnoreCase))) ||
                                (!string.IsNullOrWhiteSpace(exp.Duration) && (
                                    exp.Duration.Contains("present", StringComparison.OrdinalIgnoreCase) ||
                                    exp.Duration.Contains("hiện tại", StringComparison.OrdinalIgnoreCase) ||
                                    exp.Duration.Contains("nay", StringComparison.OrdinalIgnoreCase)));

                var endDate = isCurrent ? null : ParseDateOnly(exp.EndDate);

                var company = string.IsNullOrWhiteSpace(exp.Company) ? string.Empty : exp.Company.Trim();
                var jobTitle = string.IsNullOrWhiteSpace(exp.JobTitle) ? null : exp.JobTitle.Trim();

                experiences.Add(new CvExperienceDto(
                    company,
                    jobTitle,
                    parsedStartDate.Value,
                    endDate,
                    isCurrent,
                    exp.Description
                ));
            }
        }

        // 3. Education
        var educations = new List<CvEducationDto>();
        if (source.Education != null)
        {
            foreach (var edu in source.Education)
            {
                var institution = string.IsNullOrWhiteSpace(edu.Institution) ? string.Empty : edu.Institution.Trim();
                var degree = string.IsNullOrWhiteSpace(edu.Degree) ? null : edu.Degree.Trim();

                if (string.IsNullOrEmpty(institution) && string.IsNullOrEmpty(degree))
                {
                    continue;
                }

                int? gradYear = null;
                if (!string.IsNullOrWhiteSpace(edu.GraduationYear) &&
                    int.TryParse(edu.GraduationYear.Trim(), out var parsedYear))
                {
                    gradYear = parsedYear;
                }

                educations.Add(new CvEducationDto(
                    institution,
                    degree,
                    edu.FieldOfStudy,
                    null,
                    gradYear,
                    null
                ));
            }
        }

        // 4. Projects
        var projects = new List<CvProjectDto>();
        if (source.Projects != null)
        {
            foreach (var proj in source.Projects)
            {
                var name = proj.Name?.Trim();
                if (string.IsNullOrWhiteSpace(name))
                {
                    // AI-DEMO-004: Project không tên: Bỏ qua project, không tự đặt tên "Project"
                    continue;
                }

                var techs = proj.Technologies != null && proj.Technologies.Count > 0
                    ? string.Join(", ", proj.Technologies)
                    : null;

                projects.Add(new CvProjectDto(
                    name,
                    null,
                    null,
                    null,
                    false,
                    proj.Description,
                    techs
                ));
            }
        }

        return new StructuredCvDataDto(
            source.FullName ?? string.Empty,
            source.Email,
            source.Phone,
            source.CareerSummary,
            combinedSkills,
            experiences,
            educations,
            projects
        );
    }

    private static DateOnly? ParseDateOnly(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw)) return null;

        var cleaned = raw.Trim();
        if (DateOnly.TryParse(cleaned, out var parsed))
            return parsed;

        // Try YYYY-MM
        if (System.Text.RegularExpressions.Regex.IsMatch(cleaned, @"^\d{4}-\d{1,2}$"))
        {
            var parts = cleaned.Split('-');
            if (int.TryParse(parts[0], out var year) && int.TryParse(parts[1], out var month))
            {
                return new DateOnly(year, Math.Clamp(month, 1, 12), 1);
            }
        }

        // Try YYYY
        if (System.Text.RegularExpressions.Regex.IsMatch(cleaned, @"^\d{4}$"))
        {
            if (int.TryParse(cleaned, out var year))
            {
                return new DateOnly(year, 1, 1);
            }
        }

        return null;
    }
}

