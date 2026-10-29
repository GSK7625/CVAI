using FluentValidation;
using FutureCV.Application.Features.Admin.DTOs;

namespace FutureCV.Application.Features.Admin.Validators;

public class ResolveJobReportValidator : AbstractValidator<ResolveJobReportRequest>
{
    private static readonly string[] AllowedActions = ["Dismiss", "BanJob"];

    public ResolveJobReportValidator()
    {
        RuleFor(x => x.Action)
            .NotEmpty().WithMessage("Action is required.")
            .Must(action => AllowedActions.Contains(action))
            .WithMessage("Action must be either 'Dismiss' or 'BanJob'.");

        RuleFor(x => x.AdminNote)
            .MaximumLength(2000).WithMessage("Admin note must not exceed 2000 characters.")
            .When(x => !string.IsNullOrEmpty(x.AdminNote));
    }
}
