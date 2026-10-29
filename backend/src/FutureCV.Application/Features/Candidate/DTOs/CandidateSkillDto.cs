using FutureCV.Domain.Enums;

namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record CandidateSkillDto(
    Guid SkillId,
    SkillLevel Level,
    int? Years);
