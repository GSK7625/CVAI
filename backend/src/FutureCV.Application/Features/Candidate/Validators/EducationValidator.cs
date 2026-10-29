using FluentValidation;
using FutureCV.Application.Features.Candidate.DTOs;

namespace FutureCV.Application.Features.Candidate.Validators;

public class EducationValidator : AbstractValidator<EducationDto>
{
    public EducationValidator()
    {
        RuleFor(x => x.School)
            .NotEmpty().WithMessage("School name is required.")
            .MaximumLength(300).WithMessage("School name must not exceed 300 characters.");

        RuleFor(x => x.Degree)
            .MaximumLength(150).WithMessage("Degree must not exceed 150 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.Degree));

        RuleFor(x => x.Major)
            .MaximumLength(150).WithMessage("Major must not exceed 150 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.Major));

        RuleFor(x => x.StartYear)
            .InclusiveBetween(1950, DateTime.UtcNow.Year)
            .WithMessage($"Start year must be between 1950 and {DateTime.UtcNow.Year}.")
            .When(x => x.StartYear.HasValue);

        RuleFor(x => x.EndYear)
            .InclusiveBetween(1950, DateTime.UtcNow.Year + 10)
            .WithMessage("End year is out of valid range.")
            .GreaterThanOrEqualTo(x => x.StartYear ?? 0)
            .WithMessage("End year must be greater than or equal to start year.")
            .When(x => x.EndYear.HasValue);
    }
}
