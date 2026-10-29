namespace FutureCV.Application.Features.Auth.DTOs;

public record RegisterRequest(
    string Email,
    string Password,
    string ConfirmPassword,
    string Role
);
