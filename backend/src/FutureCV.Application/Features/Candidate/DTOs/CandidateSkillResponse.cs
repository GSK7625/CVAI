namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record CandidateSkillResponse(
    Guid SkillId,
    string SkillName,
    string? Category,
    string Level,
    int? Years);
