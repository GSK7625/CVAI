namespace FutureCV.Application.Features.Auth.DTOs;

public record ChangePasswordRequest(
    string CurrentPassword,
    string NewPassword,
    string ConfirmNewPassword
);
