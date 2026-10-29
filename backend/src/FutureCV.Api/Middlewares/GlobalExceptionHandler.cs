using FutureCV.Domain.Exceptions;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Middlewares;

/// <summary>
/// Global exception handler implementing .NET 8 IExceptionHandler.
/// Intercepts unhandled exceptions and formats responses as RFC 7807 ProblemDetails.
/// </summary>
public class GlobalExceptionHandler : IExceptionHandler
{
    private readonly ILogger<GlobalExceptionHandler> _logger;
    private readonly IHostEnvironment _env;

    public GlobalExceptionHandler(
        ILogger<GlobalExceptionHandler> logger,
        IHostEnvironment env)
    {
        _logger = logger;
        _env = env;
    }

    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext,
        Exception exception,
        CancellationToken cancellationToken)
    {
        var (statusCode, problemDetails) = exception switch
        {
            DomainException domainException => HandleDomainException(httpContext, domainException),
            _ => HandleUnhandledException(httpContext, exception)
        };

        httpContext.Response.StatusCode = statusCode;
        httpContext.Response.ContentType = "application/problem+json";

        await httpContext.Response.WriteAsJsonAsync(problemDetails, cancellationToken);

        return true;
    }

    private (int StatusCode, ProblemDetails Details) HandleDomainException(
        HttpContext context,
        DomainException exception)
    {
        _logger.LogWarning(
            exception,
            "Domain rule violation occurred on {Path}: {Message}",
            context.Request.Path,
            exception.Message);

        var details = new ProblemDetails
        {
            Status = StatusCodes.Status400BadRequest,
            Title = "Domain Rule Violation",
            Detail = exception.Message,
            Instance = context.Request.Path,
            Extensions =
            {
                ["traceId"] = context.TraceIdentifier
            }
        };

        return (StatusCodes.Status400BadRequest, details);
    }

    private (int StatusCode, ProblemDetails Details) HandleUnhandledException(
        HttpContext context,
        Exception exception)
    {
        _logger.LogError(
            exception,
            "Unhandled exception occurred while processing {Method} {Path}",
            context.Request.Method,
            context.Request.Path);

        var detail = _env.IsDevelopment()
            ? exception.Message
            : "An unexpected error occurred. Please try again later or contact support.";

        var details = new ProblemDetails
        {
            Status = StatusCodes.Status500InternalServerError,
            Title = "Internal Server Error",
            Detail = detail,
            Instance = context.Request.Path,
            Extensions =
            {
                ["traceId"] = context.TraceIdentifier
            }
        };
        return (StatusCodes.Status500InternalServerError, details);
    }
}
