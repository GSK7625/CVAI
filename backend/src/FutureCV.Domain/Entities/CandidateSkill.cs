using FutureCV.Domain.Enums;

namespace FutureCV.Domain.Entities;

// Junction entity for the CandidateSkills table — composite PK (CandidateId, SkillId)
public class CandidateSkill
{
    public Guid CandidateId { get; set; }
    public Guid SkillId { get; set; }
    public SkillLevel Level { get; set; }
    public int? Years { get; set; }

    public Candidate Candidate { get; set; } = null!;
    public Skill Skill { get; set; } = null!;
}
