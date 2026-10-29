namespace FutureCV.Application.Common.Models;

/// <summary>
/// Discriminated union representing the outcome of an application service operation.
/// Does NOT contain HTTP-specific information (no StatusCode).
/// The API/Controller layer is responsible for mapping error types to HTTP responses.
/// </summary>
public class ServiceResult<T>
{
    public bool IsSuccess { get; init; }
    public T? Data { get; init; }
    public string? ErrorMessage { get; init; }
    public ServiceErrorType ErrorType { get; init; }
}

/// <summary>
/// Categorizes the failure reason so the Controller can decide the correct HTTP status code.
/// </summary>
public enum ServiceErrorType
{
    None = 0,

    /// <summary>400 — Input validation failed or business rule violated.</summary>
    Validation,

    /// <summary>404 — The requested resource does not exist.</summary>
    NotFound,

    /// <summary>401 — Authentication failed or caller is unauthenticated.</summary>
    Unauthorized,

    /// <summary>403 — The caller is not permitted to perform this action.</summary>
    Forbidden,

    /// <summary>409 — Resource already exists or conflicts with current state.</summary>
    Conflict,

    /// <summary>500 — Unexpected infrastructure failure (DB, external service, etc.).</summary>
    Infrastructure,
}

/// <summary>
/// Static factory methods for <see cref="ServiceResult{T}"/>.
/// </summary>
public static class ServiceResult
{
    public static ServiceResult<T> Success<T>(T data) =>
        new() { IsSuccess = true, Data = data };

    public static ServiceResult<T> Failure<T>(
        string errorMessage,
        ServiceErrorType errorType = ServiceErrorType.Validation) =>
        new() { IsSuccess = false, ErrorMessage = errorMessage, ErrorType = errorType };

    public static ServiceResult<T> NotFound<T>(string errorMessage) =>
        Failure<T>(errorMessage, ServiceErrorType.NotFound);

    public static ServiceResult<T> Unauthorized<T>(string errorMessage) =>
        Failure<T>(errorMessage, ServiceErrorType.Unauthorized);

    public static ServiceResult<T> Forbidden<T>(string errorMessage) =>
        Failure<T>(errorMessage, ServiceErrorType.Forbidden);

    public static ServiceResult<T> Conflict<T>(string errorMessage) =>
        Failure<T>(errorMessage, ServiceErrorType.Conflict);

    public static ServiceResult<T> InfrastructureError<T>(string errorMessage) =>
        Failure<T>(errorMessage, ServiceErrorType.Infrastructure);
}
