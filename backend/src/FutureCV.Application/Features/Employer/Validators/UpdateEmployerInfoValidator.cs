using FluentValidation;
using FutureCV.Application.Features.Employer.DTOs;

namespace FutureCV.Application.Features.Employer.Validators;

public class UpdateEmployerInfoValidator : AbstractValidator<UpdateEmployerInfoRequest>
{
    private const string VnPhonePattern = @"^0\d{9}$";

    public UpdateEmployerInfoValidator()
    {
        RuleFor(x => x.FullName)
            .NotEmpty().WithMessage("Full name is required.")
            .MaximumLength(200).WithMessage("Full name must not exceed 200 characters.");

        RuleFor(x => x.Position)
            .MaximumLength(200).WithMessage("Position must not exceed 200 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.Position));

        RuleFor(x => x.Gender)
            .Must(g => g is "Male" or "Female")
            .WithMessage("Gender must be 'Male' or 'Female'.")
            .When(x => !string.IsNullOrWhiteSpace(x.Gender));

        RuleFor(x => x.Phone)
            .Matches(VnPhonePattern)
            .WithMessage("Phone number must be a valid Vietnamese number (e.g. 0912345678).")
            .When(x => !string.IsNullOrWhiteSpace(x.Phone));
    }
}
