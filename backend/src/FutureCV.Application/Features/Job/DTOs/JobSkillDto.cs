namespace FutureCV.Application.Features.Job.DTOs;

public sealed record JobSkillDto(
    Guid SkillId,
    bool IsRequired = true);

public sealed record JobSkillResponse(
    Guid SkillId,
    string SkillName,
    string? Category,
    bool IsRequired);
