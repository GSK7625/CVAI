using FluentValidation;
using FutureCV.Application.Features.Auth.DTOs;

namespace FutureCV.Application.Features.Auth.Validators;

public class GoogleLoginRequestValidator : AbstractValidator<GoogleLoginRequest>
{
    public GoogleLoginRequestValidator()
    {
        RuleFor(x => x.GoogleIdToken)
            .NotEmpty().WithMessage("Google ID Token is required.");
    }
}
