using FluentValidation;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Features.Auth.DTOs;

namespace FutureCV.Application.Features.Auth.Validators;

public class RefreshTokenRequestValidator : AbstractValidator<RefreshTokenRequest>
{
    public RefreshTokenRequestValidator(ITokenCookieService tokenCookieService)
    {
        RuleFor(x => x)
            .Must(req => !string.IsNullOrWhiteSpace(req.RefreshToken) || !string.IsNullOrWhiteSpace(tokenCookieService.GetRefreshToken()))
            .WithMessage("Refresh token is required.");
    }
}
