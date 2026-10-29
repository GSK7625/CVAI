using FluentValidation;
using FutureCV.Application.Features.Candidate.DTOs;

namespace FutureCV.Application.Features.Candidate.Validators;

public class UpdateCandidateInfoValidator : AbstractValidator<UpdateCandidateInfoRequest>
{
    private const string VnPhonePattern = @"^0\d{9}$";

    public UpdateCandidateInfoValidator()
    {
        RuleFor(x => x.FullName)
            .NotEmpty().WithMessage("Full name is required.")
            .MaximumLength(200).WithMessage("Full name must not exceed 200 characters.");

        RuleFor(x => x.Phone)
            .Matches(VnPhonePattern)
            .WithMessage("Phone number must be a valid Vietnamese number (e.g. 0912345678).")
            .When(x => !string.IsNullOrWhiteSpace(x.Phone));

        RuleFor(x => x.Gender)
            .Must(g => g is "Male" or "Female")
            .WithMessage("Gender must be 'Male' or 'Female'.")
            .When(x => !string.IsNullOrWhiteSpace(x.Gender));

        RuleFor(x => x.DesiredPosition)
            .MaximumLength(200).WithMessage("Desired position must not exceed 200 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.DesiredPosition));

        RuleFor(x => x.DesiredSalaryMin)
            .GreaterThanOrEqualTo(0).WithMessage("Minimum salary must be 0 or greater.")
            .When(x => x.DesiredSalaryMin.HasValue);

        RuleFor(x => x.DesiredSalaryMax)
            .GreaterThanOrEqualTo(0).WithMessage("Maximum salary must be 0 or greater.")
            .GreaterThanOrEqualTo(x => x.DesiredSalaryMin ?? 0)
            .WithMessage("Maximum salary must be greater than or equal to minimum salary.")
            .When(x => x.DesiredSalaryMax.HasValue);
    }
}
