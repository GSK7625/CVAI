namespace FutureCV.Application.Features.Auth.DTOs;

public record ResetPasswordRequest(
    string Email,
    string Token,
    string NewPassword,
    string ConfirmNewPassword
);
