using FluentValidation;
using FutureCV.Application.Features.JobApplication.DTOs;

namespace FutureCV.Application.Features.JobApplication.Validators;

public class UpdateApplicationStatusValidator : AbstractValidator<UpdateApplicationStatusRequest>
{
    private static readonly string[] AllowedStatuses = ["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"];

    public UpdateApplicationStatusValidator()
    {
        RuleFor(x => x.NewStatus)
            .NotEmpty().WithMessage("New status is required.")
            .Must(status => AllowedStatuses.Contains(status))
            .WithMessage($"Status must be one of: {string.Join(", ", AllowedStatuses)}.");

        RuleFor(x => x.Reason)
            .MaximumLength(500).WithMessage("Reason must not exceed 500 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.Reason));
    }
}
