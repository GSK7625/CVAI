namespace FutureCV.Application.Features.Job.DTOs;

public sealed record LocationResponse(
    Guid Id,
    string Name,
    Guid? ParentId);

public sealed record JobCategoryResponse(
    Guid Id,
    string Name,
    Guid? ParentId);

public sealed record JobLevelResponse(
    Guid Id,
    string Name);

public sealed record EmploymentTypeResponse(
    Guid Id,
    string Name);
