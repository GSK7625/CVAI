using FluentValidation;
using FutureCV.Application.Features.Candidate.DTOs;

namespace FutureCV.Application.Features.Candidate.Validators;

public class ExperienceValidator : AbstractValidator<ExperienceDto>
{
    public ExperienceValidator()
    {
        RuleFor(x => x.CompanyName)
            .NotEmpty().WithMessage("Company name is required.")
            .MaximumLength(300).WithMessage("Company name must not exceed 300 characters.");

        RuleFor(x => x.Position)
            .MaximumLength(200).WithMessage("Position must not exceed 200 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.Position));

        RuleFor(x => x.StartDate)
            .NotEmpty().WithMessage("Start date is required.")
            .LessThanOrEqualTo(DateOnly.FromDateTime(DateTime.UtcNow))
            .WithMessage("Start date cannot be in the future.");

        // If IsCurrent = true, EndDate must be null
        RuleFor(x => x.EndDate)
            .Null().WithMessage("End date must be empty when 'Currently working here' is checked.")
            .When(x => x.IsCurrent);

        // If IsCurrent = false, EndDate must be provided and >= StartDate
        RuleFor(x => x.EndDate)
            .NotNull().WithMessage("End date is required when not currently working here.")
            .GreaterThanOrEqualTo(x => x.StartDate)
            .WithMessage("End date must be on or after start date.")
            .When(x => !x.IsCurrent);
    }
}
