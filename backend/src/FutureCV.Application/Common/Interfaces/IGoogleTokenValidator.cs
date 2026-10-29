using FutureCV.Application.Common.Models;

namespace FutureCV.Application.Common.Interfaces;

public interface IGoogleTokenValidator
{
    Task<GoogleTokenPayload?> ValidateAsync(string idToken);
}
