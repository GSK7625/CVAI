using FluentValidation;
using FutureCV.Application.Features.Candidate.DTOs;

namespace FutureCV.Application.Features.Candidate.Validators;

public class CandidateSkillValidator : AbstractValidator<CandidateSkillDto>
{
    public CandidateSkillValidator()
    {
        RuleFor(x => x.SkillId)
            .NotEmpty().WithMessage("Skill ID is required.");

        RuleFor(x => x.Level)
            .IsInEnum().WithMessage("Skill level must be Beginner, Intermediate, or Advanced.");

        RuleFor(x => x.Years)
            .GreaterThanOrEqualTo(0).WithMessage("Years of experience must be 0 or greater.")
            .LessThanOrEqualTo(50).WithMessage("Years of experience must not exceed 50.")
            .When(x => x.Years.HasValue);
    }
}
