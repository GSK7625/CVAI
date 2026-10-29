namespace FutureCV.Application.Features.Auth.DTOs;

public record LogoutRequest(string? RefreshToken = null);
