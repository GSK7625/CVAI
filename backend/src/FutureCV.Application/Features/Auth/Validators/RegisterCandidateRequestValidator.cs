using FluentValidation;
using FutureCV.Application.Features.Auth.DTOs;

namespace FutureCV.Application.Features.Auth.Validators;

public class RegisterCandidateRequestValidator : AbstractValidator<RegisterCandidateRequest>
{
    public RegisterCandidateRequestValidator()
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
    }
}
