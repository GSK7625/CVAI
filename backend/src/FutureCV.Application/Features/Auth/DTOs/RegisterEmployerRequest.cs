namespace FutureCV.Application.Features.Auth.DTOs;

public class RegisterEmployerRequest
{
    // 1. Account Info
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public string ConfirmPassword { get; set; } = string.Empty;

    // 2. Employer Profile Info
    public string FullName { get; set; } = string.Empty;
    public string Gender { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;

    // 3. Company Info
    public string CompanyName { get; set; } = string.Empty;
    public string? LocationId { get; set; }
    public string? WardName { get; set; }
}
