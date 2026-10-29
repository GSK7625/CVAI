using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using Google.Apis.Auth;
using Microsoft.Extensions.Configuration;

namespace FutureCV.Infrastructure.Identity;

public class GoogleTokenValidator : IGoogleTokenValidator
{
    private readonly IConfiguration _configuration;

    public GoogleTokenValidator(IConfiguration configuration)
    {
        _configuration = configuration;
    }

    public async Task<GoogleTokenPayload?> ValidateAsync(string idToken)
    {
        try
        {
            var settings = new GoogleJsonWebSignature.ValidationSettings
            {
                Audience = new[] { _configuration["GoogleAuth:ClientId"] }
            };
            
            var payload = await GoogleJsonWebSignature.ValidateAsync(idToken, settings);
            
            if (payload == null) 
                return null;

            return new GoogleTokenPayload
            {
                Email = payload.Email,
                Subject = payload.Subject,
                Name = payload.Name,
                EmailVerified = payload.EmailVerified
            };
        }
        catch (Exception)
        {
            return null; // Invalid token or signature
        }
    }
}
