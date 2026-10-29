namespace FutureCV.Application.Features.Auth.DTOs;

public class GoogleRegisterEmployerRequest
{
    public string GoogleIdToken { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;
    public string Gender { get; set; } = string.Empty;
    public string CompanyName { get; set; } = string.Empty;
    public string? LocationId { get; set; }
    public string? WardName { get; set; }
}
