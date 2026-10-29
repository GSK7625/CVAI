using FluentValidation;
using FutureCV.Application.Features.Auth.DTOs;
using FutureCV.Domain.Enums;

namespace FutureCV.Application.Features.Auth.Validators;

public class RegisterEmployerRequestValidator : AbstractValidator<RegisterEmployerRequest>
{
    public RegisterEmployerRequestValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty().WithMessage("Email is required.")
            .EmailAddress().WithMessage("A valid email address is required.")
            .MaximumLength(256).WithMessage("Email must not exceed 256 characters.");

        RuleFor(x => x.Password)
            .NotEmpty().WithMessage("Password is required.")
            .MinimumLength(6).WithMessage("Password must be between 6 and 25 characters.")
            .MaximumLength(25).WithMessage("Password must be between 6 and 25 characters.")
            .Matches(@"[A-Z]").WithMessage("Password must contain at least one uppercase letter.")
            .Matches(@"[a-z]").WithMessage("Password must contain at least one lowercase letter.")
            .Matches(@"[0-9]").WithMessage("Password must contain at least one numeric digit.");

        RuleFor(x => x.ConfirmPassword)
            .NotEmpty().WithMessage("Confirm password is required.")
            .Equal(x => x.Password).WithMessage("Passwords do not match.");

        RuleFor(x => x.FullName)
            .NotEmpty().WithMessage("Full Name is required.")
            .MaximumLength(200).WithMessage("Full Name must not exceed 200 characters.");

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
