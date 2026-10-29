using FluentValidation;
using FutureCV.Application.Features.Job.DTOs;

namespace FutureCV.Application.Features.Job.Validators;

public class CreateJobValidator : AbstractValidator<CreateJobRequest>
{
    public CreateJobValidator()
    {
        RuleFor(x => x.Title)
            .NotEmpty().WithMessage("Job title is required.")
            .MaximumLength(300).WithMessage("Job title must not exceed 300 characters.");

        RuleFor(x => x.Description)
            .NotEmpty().WithMessage("Job description is required.");

        RuleFor(x => x.PositionsCount)
            .GreaterThan(0).WithMessage("Positions count must be at least 1.");

        RuleFor(x => x.SalaryMin)
            .GreaterThanOrEqualTo(0).WithMessage("Minimum salary must not be negative.")
            .When(x => x.SalaryMin.HasValue);

        RuleFor(x => x.SalaryMax)
            .GreaterThanOrEqualTo(0).WithMessage("Maximum salary must not be negative.")
            .When(x => x.SalaryMax.HasValue);

        RuleFor(x => x)
            .Must(x => !x.SalaryMin.HasValue || !x.SalaryMax.HasValue || x.SalaryMax >= x.SalaryMin)
            .WithMessage("Maximum salary must be greater than or equal to minimum salary.")
            .When(x => x.SalaryMin.HasValue && x.SalaryMax.HasValue);

        RuleFor(x => x)
            .Must(x => !x.ExperienceYearsMin.HasValue || !x.ExperienceYearsMax.HasValue || x.ExperienceYearsMax >= x.ExperienceYearsMin)
            .WithMessage("Maximum experience years must be greater than or equal to minimum experience years.")
            .When(x => x.ExperienceYearsMin.HasValue && x.ExperienceYearsMax.HasValue);

        RuleFor(x => x.Deadline)
            .Must(deadline => !deadline.HasValue || deadline.Value > DateTime.UtcNow)
            .WithMessage("Deadline must be in the future.")
            .When(x => x.Deadline.HasValue);
    }
}
