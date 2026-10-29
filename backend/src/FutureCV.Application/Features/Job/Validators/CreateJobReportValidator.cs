using FluentValidation;
using FutureCV.Application.Features.Job.DTOs;

namespace FutureCV.Application.Features.Job.Validators;

public class CreateJobReportValidator : AbstractValidator<CreateJobReportRequest>
{
    public CreateJobReportValidator()
    {
        RuleFor(x => x.Reason)
            .NotEmpty().WithMessage("Report reason is required.")
            .MaximumLength(100).WithMessage("Report reason must not exceed 100 characters.");

        RuleFor(x => x.Details)
            .MaximumLength(2000).WithMessage("Report details must not exceed 2000 characters.")
            .When(x => !string.IsNullOrEmpty(x.Details));
    }
}
