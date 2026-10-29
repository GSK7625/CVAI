using FluentValidation;
using FutureCV.Application.Features.Employer.DTOs;

namespace FutureCV.Application.Features.Employer.Validators;

public class UpdateCompanyInfoValidator : AbstractValidator<UpdateCompanyInfoRequest>
{
    public UpdateCompanyInfoValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Company name is required.")
            .MaximumLength(300).WithMessage("Company name must not exceed 300 characters.");

        RuleFor(x => x.Scale)
            .MaximumLength(100).WithMessage("Scale must not exceed 100 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.Scale));

        RuleFor(x => x.Industry)
            .MaximumLength(100).WithMessage("Industry must not exceed 100 characters.")
            .When(x => !string.IsNullOrWhiteSpace(x.Industry));

        RuleFor(x => x.WebsiteUrl)
            .Must(url => Uri.TryCreate(url, UriKind.Absolute, out _))
            .WithMessage("Website URL must be a valid URL.")
            .When(x => !string.IsNullOrWhiteSpace(x.WebsiteUrl));
    }
}
