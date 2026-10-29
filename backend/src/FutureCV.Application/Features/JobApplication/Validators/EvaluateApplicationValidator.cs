using FluentValidation;
using FutureCV.Application.Features.JobApplication.DTOs;

namespace FutureCV.Application.Features.JobApplication.Validators;

public class EvaluateApplicationValidator : AbstractValidator<EvaluateApplicationRequest>
{
    public EvaluateApplicationValidator()
    {
        RuleFor(x => x.Rating)
            .InclusiveBetween(1, 5).WithMessage("Rating must be between 1 and 5 stars.");

        RuleFor(x => x.EvaluationLabel)
            .MaximumLength(100).WithMessage("Evaluation label must not exceed 100 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.EvaluationLabel));

        RuleFor(x => x.PrivateNotes)
            .MaximumLength(2000).WithMessage("Private notes must not exceed 2000 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.PrivateNotes));
    }
}
