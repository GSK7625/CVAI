namespace FutureCV.Application.Features.Auth.DTOs;

public record LoginRequest(
    string Email,
    string Password
);
