using System.Diagnostics;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.AiMatching.DTOs;
using FutureCV.Infrastructure.Configurations;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace FutureCV.Infrastructure.Services;

/// <summary>
/// Typed HTTP client adapter connecting ASP.NET Core to the Python FastAPI Matching Service.
/// Implements internal service authentication, correlation ID propagation, bounds validation,
/// and resilient infrastructure error mapping.
/// </summary>
public class AiMatchingHttpClient : IAiMatchingClient
{
    private const string InternalApiKeyHeader = "X-Internal-API-Key";
    private const string CorrelationIdHeader = "X-Correlation-ID";

    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;
    private readonly ILogger<AiMatchingHttpClient> _logger;
    private readonly AiServiceOptions _options;
    private readonly JsonSerializerOptions _jsonOptions;

    public AiMatchingHttpClient(
        HttpClient httpClient,
        IConfiguration configuration,
        ILogger<AiMatchingHttpClient> logger,
        IOptions<AiServiceOptions>? options = null)
    {
        _httpClient = httpClient;
        _configuration = configuration;
        _logger = logger;
        _options = options?.Value ?? new AiServiceOptions();

        _jsonOptions = new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        };

        // 1. Configure BaseAddress from typed options or configuration fallback
        if (_httpClient.BaseAddress == null)
        {
            var baseUrl = !string.IsNullOrWhiteSpace(_options.BaseUrl)
                ? _options.BaseUrl
                : (_configuration["AiService:BaseUrl"] ?? "http://localhost:8000");

            _httpClient.BaseAddress = new Uri(baseUrl.TrimEnd('/') + "/");
        }

        // 2. Configure Timeout
        var timeoutSeconds = _options.TimeoutSeconds > 0
            ? _options.TimeoutSeconds
            : (double.TryParse(_configuration["AiService:TimeoutSeconds"], out var t) && t > 0 ? t : 90.0);

        if (_httpClient.Timeout == TimeSpan.FromSeconds(100)) // default HttpClient timeout
        {
            _httpClient.Timeout = TimeSpan.FromSeconds(timeoutSeconds);
        }
    }

    public async Task<ServiceResult<AiMatchResultDto>> MatchAsync(
        AiMatchRequest request,
        string? correlationId = null,
        CancellationToken cancellationToken = default)
    {
        var effectiveCorrelationId = !string.IsNullOrWhiteSpace(correlationId)
            ? correlationId
            : Guid.NewGuid().ToString("N");

        try
        {
            var requestUri = "api/v1/job/match";
            using var httpRequest = new HttpRequestMessage(HttpMethod.Post, requestUri);

            // 1. Attach Internal API Key
            var apiKey = !string.IsNullOrWhiteSpace(_options.ApiKey)
                ? _options.ApiKey
                : _configuration["AiService:ApiKey"];

            if (!string.IsNullOrWhiteSpace(apiKey))
            {
                httpRequest.Headers.Add(InternalApiKeyHeader, apiKey);
            }

            // 2. Attach Correlation ID for distributed tracing
            httpRequest.Headers.Add(CorrelationIdHeader, effectiveCorrelationId);

            // 3. Serialize payload
            var jsonPayload = JsonSerializer.Serialize(request, _jsonOptions);
            httpRequest.Content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

            _logger.LogInformation(
                "Calling AI Matching Service at {Endpoint} [CorrelationId: {CorrelationId}]",
                requestUri,
                effectiveCorrelationId);

            // 4. Execute HTTP Call with duration timing
            var stopwatch = Stopwatch.StartNew();
            using var response = await _httpClient.SendAsync(httpRequest, cancellationToken);
            stopwatch.Stop();
            var durationMs = stopwatch.ElapsedMilliseconds;

            var responseBody = await response.Content.ReadAsStringAsync(cancellationToken);

            if (response.IsSuccessStatusCode)
            {
                // Reject empty or whitespace response body on successful status
                if (string.IsNullOrWhiteSpace(responseBody))
                {
                    _logger.LogError(
                        "AI Matching Service returned empty or whitespace response body in {DurationMs}ms [CorrelationId: {CorrelationId}]",
                        durationMs,
                        effectiveCorrelationId);
                    return ServiceResult.Failure<AiMatchResultDto>(
                        "AI matching service returned an empty response.",
                        ServiceErrorType.Infrastructure);
                }

                AiMatchResultDto? matchResult;
                try
                {
                    matchResult = JsonSerializer.Deserialize<AiMatchResultDto>(responseBody, _jsonOptions);
                }
                catch (JsonException ex)
                {
                    _logger.LogError(
                        ex,
                        "AI Matching Service returned malformed JSON body at {Endpoint} [CorrelationId: {CorrelationId}]",
                        requestUri,
                        effectiveCorrelationId);
                    return ServiceResult.Failure<AiMatchResultDto>(
                        "Failed to parse response from AI matching service.",
                        ServiceErrorType.Infrastructure);
                }

                if (matchResult == null)
                {
                    _logger.LogError(
                        "AI Matching Service returned null payload at {Endpoint} [CorrelationId: {CorrelationId}]",
                        requestUri,
                        effectiveCorrelationId);
                    return ServiceResult.Failure<AiMatchResultDto>(
                        "Failed to parse response from AI matching service.",
                        ServiceErrorType.Infrastructure);
                }

                // Bounds validation: MatchScore must be within [0, 100]
                if (matchResult.MatchScore < 0 || matchResult.MatchScore > 100)
                {
                    _logger.LogError(
                        "AI Matching Service returned out-of-bounds match score {Score} [CorrelationId: {CorrelationId}]",
                        matchResult.MatchScore,
                        effectiveCorrelationId);
                    return ServiceResult.Failure<AiMatchResultDto>(
                        $"AI matching service returned invalid match score: {matchResult.MatchScore}. Expected between 0 and 100.",
                        ServiceErrorType.Infrastructure);
                }

                _logger.LogInformation(
                    "AI Matching succeeded: Score={Score} in {DurationMs}ms at {Endpoint} [CorrelationId: {CorrelationId}]",
                    matchResult.MatchScore,
                    durationMs,
                    requestUri,
                    effectiveCorrelationId);

                return ServiceResult.Success(matchResult);
            }

            // 5. Handle Error Responses without logging response body to protect PII
            string? errorCode = null;
            string? errorMessage = null;
            if (!string.IsNullOrWhiteSpace(responseBody))
            {
                try
                {
                    var errorObj = JsonSerializer.Deserialize<AiErrorResponseDto>(responseBody, _jsonOptions);
                    errorCode = errorObj?.ErrorCode;
                    errorMessage = errorObj?.Message;

                    if (string.IsNullOrWhiteSpace(errorCode))
                    {
                        using var doc = JsonDocument.Parse(responseBody);
                        if (doc.RootElement.TryGetProperty("code", out var codeProp))
                        {
                            errorCode = codeProp.GetString();
                        }
                    }
                }
                catch
                {
                    // Fallback if error body is not standard AiErrorResponseDto
                }
            }

            _logger.LogWarning(
                "AI Matching Service returned HTTP {StatusCode}, ErrorCode={ErrorCode} in {DurationMs}ms at {Endpoint} [CorrelationId: {CorrelationId}]",
                (int)response.StatusCode,
                errorCode ?? "N/A",
                durationMs,
                requestUri,
                effectiveCorrelationId);

            if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            {
                return ServiceResult.Failure<AiMatchResultDto>(
                    "Internal authentication to AI service failed.",
                    ServiceErrorType.Unauthorized);
            }

            if (response.StatusCode == System.Net.HttpStatusCode.UnprocessableEntity ||
                response.StatusCode == System.Net.HttpStatusCode.BadRequest)
            {
                return ServiceResult.Failure<AiMatchResultDto>(
                    errorMessage ?? "Invalid matching request parameters.",
                    ServiceErrorType.Validation);
            }

            return ServiceResult.Failure<AiMatchResultDto>(
                $"AI service returned error status ({response.StatusCode}).",
                ServiceErrorType.Infrastructure);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            _logger.LogError(
                "AI Matching Service request timed out [CorrelationId: {CorrelationId}]",
                effectiveCorrelationId);
            return ServiceResult.Failure<AiMatchResultDto>(
                "AI matching service request timed out.",
                ServiceErrorType.Infrastructure);
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(
                ex,
                "Network exception occurred while connecting to AI Matching Service [CorrelationId: {CorrelationId}]",
                effectiveCorrelationId);
            return ServiceResult.Failure<AiMatchResultDto>(
                "Unable to connect to AI matching service.",
                ServiceErrorType.Infrastructure);
        }
        catch (Exception ex)
        {
            _logger.LogError(
                ex,
                "Unexpected error during AI Matching Service invocation [CorrelationId: {CorrelationId}]",
                effectiveCorrelationId);
            return ServiceResult.Failure<AiMatchResultDto>(
                "An unexpected error occurred during AI matching.",
                ServiceErrorType.Infrastructure);
        }
    }
}
