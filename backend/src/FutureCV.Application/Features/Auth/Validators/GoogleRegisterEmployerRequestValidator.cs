using FluentValidation;
using FutureCV.Application.Features.Auth.DTOs;
using FutureCV.Domain.Enums;

namespace FutureCV.Application.Features.Auth.Validators;

public class GoogleRegisterEmployerRequestValidator : AbstractValidator<GoogleRegisterEmployerRequest>
{
    public GoogleRegisterEmployerRequestValidator()
    {
        RuleFor(x => x.GoogleIdToken)
            .NotEmpty().WithMessage("Google ID Token is required.");

        RuleFor(x => x.Gender)
            .NotEmpty().WithMessage("Gender is required.")
            .IsEnumName(typeof(Gender), caseSensitive: false)
            .WithMessage("Gender must be either 'Male' or 'Female'.");

        RuleFor(x => x.Phone)
            .NotEmpty().WithMessage("Phone number is required.")
            .Matches(@"^0\d{9}$").WithMessage("Phone number must be exactly 10 digits starting with 0 (e.g. 0912345678).");

        RuleFor(x => x.CompanyName)
            .NotEmpty().WithMessage("Company Name is required.")
            .MaximumLength(300).WithMessage("Company Name must not exceed 300 characters.");

        RuleFor(x => x.LocationId)
            .MaximumLength(100).WithMessage("Location ID must not exceed 100 characters.")
            .When(x => !string.IsNullOrEmpty(x.LocationId));

        RuleFor(x => x.WardName)
            .MaximumLength(150).WithMessage("Ward name must not exceed 150 characters.")
            .When(x => !string.IsNullOrEmpty(x.WardName));
    }
}
