using FluentValidation;
using FutureCV.Application.Features.JobApplication.DTOs;

namespace FutureCV.Application.Features.JobApplication.Validators;

public class ApplyJobValidator : AbstractValidator<ApplyJobRequest>
{
    public ApplyJobValidator()
    {
        RuleFor(x => x.CvId)
            .NotEmpty().WithMessage("CV must be selected for application.");

        RuleFor(x => x.CoverLetter)
            .MaximumLength(2000).WithMessage("Cover letter must not exceed 2000 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.CoverLetter));
    }
}
