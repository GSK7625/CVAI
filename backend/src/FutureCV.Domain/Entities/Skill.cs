using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

// Shared lookup table — used by both CandidateSkills and JobSkills
public class Skill : BaseEntity
{
    public string Name { get; set; } = string.Empty;
    public string? Category { get; set; }
}
