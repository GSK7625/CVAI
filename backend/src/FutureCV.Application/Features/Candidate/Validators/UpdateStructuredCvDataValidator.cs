using FluentValidation;
using FutureCV.Application.Features.Candidate.DTOs;

namespace FutureCV.Application.Features.Candidate.Validators;

public class UpdateStructuredCvDataValidator : AbstractValidator<UpdateStructuredCvDataRequest>
{
    public UpdateStructuredCvDataValidator()
    {
        RuleFor(x => x.Data).NotNull().WithMessage("Structured CV data is required.");

        When(x => x.Data != null, () =>
        {
            RuleFor(x => x.Data.FullName)
                .NotEmpty().WithMessage("Full name is required.")
                .MaximumLength(200).WithMessage("Full name must not exceed 200 characters.");

            RuleForEach(x => x.Data.Experiences).ChildRules(exp =>
            {
                exp.RuleFor(e => e.CompanyName)
                    .NotEmpty().WithMessage("Company name is required.")
                    .MaximumLength(300);

                exp.RuleFor(e => e.Position)
                    .MaximumLength(200).WithMessage("Position must not exceed 200 characters.")
                    .When(e => !string.IsNullOrWhiteSpace(e.Position));

                exp.RuleFor(e => e)
                    .Must(e => !e.EndDate.HasValue || e.EndDate >= e.StartDate)
                    .WithMessage("End date must be greater than or equal to start date.")
                    .When(e => !e.IsCurrent);
            });

            RuleForEach(x => x.Data.Educations).ChildRules(edu =>
            {
                edu.RuleFor(e => e.School)
                    .NotEmpty().WithMessage("School name is required.")
                    .MaximumLength(300);

                edu.RuleFor(e => e)
                    .Must(e => !e.StartYear.HasValue || !e.EndYear.HasValue || e.EndYear >= e.StartYear)
                    .WithMessage("End year must be greater than or equal to start year.");
            });
        });
    }
}
