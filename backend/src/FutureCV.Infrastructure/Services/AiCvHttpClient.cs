using System.Diagnostics;
using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Candidate.DTOs;
using FutureCV.Infrastructure.Configurations;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace FutureCV.Infrastructure.Services;

/// <summary>
/// HTTP client implementation for CV parsing, PDF text extraction, and quality scoring via Python FastAPI.
/// </summary>
public class AiCvHttpClient : IAiCvClient
{
    private const string InternalApiKeyHeader = "X-Internal-API-Key";
    private const string CorrelationIdHeader = "X-Correlation-ID";

    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;
    private readonly ILogger<AiCvHttpClient> _logger;
    private readonly AiServiceOptions _options;
    private readonly JsonSerializerOptions _jsonOptions;

    public AiCvHttpClient(
        HttpClient httpClient,
        IConfiguration configuration,
        ILogger<AiCvHttpClient> logger,
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

        if (_httpClient.BaseAddress == null)
        {
            var baseUrl = !string.IsNullOrWhiteSpace(_options.BaseUrl)
                ? _options.BaseUrl
                : (_configuration["AiService:BaseUrl"] ?? "http://localhost:8000");

            _httpClient.BaseAddress = new Uri(baseUrl.TrimEnd('/') + "/");
        }

        var timeoutSeconds = _options.TimeoutSeconds > 0
            ? _options.TimeoutSeconds
            : (double.TryParse(_configuration["AiService:TimeoutSeconds"], out var t) && t > 0 ? t : 90.0);

        if (_httpClient.Timeout == TimeSpan.FromSeconds(100))
        {
            _httpClient.Timeout = TimeSpan.FromSeconds(timeoutSeconds);
        }
    }

    public async Task<ServiceResult<FastApiCvAnalysisResponseDto>> AnalyzePdfAsync(
        byte[] fileBytes,
        string fileName,
        string? correlationId = null,
        CancellationToken cancellationToken = default)
    {
        var effectiveCorrelationId = !string.IsNullOrWhiteSpace(correlationId)
            ? correlationId
            : Guid.NewGuid().ToString("N");

        try
        {
            var requestUri = "api/v1/cv/analyze";
            using var httpRequest = new HttpRequestMessage(HttpMethod.Post, requestUri);

            AttachHeaders(httpRequest, effectiveCorrelationId);

            using var multipart = new MultipartFormDataContent();
            var fileContent = new ByteArrayContent(fileBytes);
            fileContent.Headers.ContentType = new MediaTypeHeaderValue("application/pdf");
            multipart.Add(fileContent, "file", fileName);

            httpRequest.Content = multipart;

            _logger.LogInformation(
                "Calling AI CV Analyze PDF at {Endpoint} for {FileName} ({Bytes} bytes) [CorrelationId: {CorrelationId}]",
                requestUri,
                fileName,
                fileBytes.Length,
                effectiveCorrelationId);

            var stopwatch = Stopwatch.StartNew();
            using var response = await _httpClient.SendAsync(
                httpRequest, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
            stopwatch.Stop();

            return await HandleResponseAsync(response, requestUri, effectiveCorrelationId, stopwatch.ElapsedMilliseconds, cancellationToken);
        }
        catch (OperationCanceledException ex) when (!cancellationToken.IsCancellationRequested)
        {
            _logger.LogError(ex, "Timeout contacting AI CV Service [CorrelationId: {CorrelationId}]", effectiveCorrelationId);
            return ServiceResult.Failure<FastApiCvAnalysisResponseDto>(
                "AI CV service timed out.", ServiceErrorType.Infrastructure);
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "HTTP network error contacting AI CV Service [CorrelationId: {CorrelationId}]", effectiveCorrelationId);
            return ServiceResult.Failure<FastApiCvAnalysisResponseDto>(
                "Failed to reach AI CV service.", ServiceErrorType.Infrastructure);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unexpected error calling AI CV Service [CorrelationId: {CorrelationId}]", effectiveCorrelationId);
            return ServiceResult.Failure<FastApiCvAnalysisResponseDto>(
                "Unexpected error during CV analysis.", ServiceErrorType.Infrastructure);
        }
    }

    public async Task<ServiceResult<FastApiCvAnalysisResponseDto>> AnalyzeTextAsync(
        string rawText,
        string? candidateId = null,
        string? correlationId = null,
        CancellationToken cancellationToken = default)
    {
        var effectiveCorrelationId = !string.IsNullOrWhiteSpace(correlationId)
            ? correlationId
            : Guid.NewGuid().ToString("N");

        try
        {
            var requestUri = "api/v1/cv/analyze-text";
            using var httpRequest = new HttpRequestMessage(HttpMethod.Post, requestUri);

            AttachHeaders(httpRequest, effectiveCorrelationId);

            var payload = new
            {
                raw_text = rawText,
                candidate_id = candidateId
            };
            var json = JsonSerializer.Serialize(payload, _jsonOptions);
            httpRequest.Content = new StringContent(json, Encoding.UTF8, "application/json");

            _logger.LogInformation(
                "Calling AI CV Analyze Text at {Endpoint} ({Chars} chars) [CorrelationId: {CorrelationId}]",
                requestUri,
                rawText.Length,
                effectiveCorrelationId);

            var stopwatch = Stopwatch.StartNew();
            using var response = await _httpClient.SendAsync(
                httpRequest, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
            stopwatch.Stop();

            return await HandleResponseAsync(response, requestUri, effectiveCorrelationId, stopwatch.ElapsedMilliseconds, cancellationToken);
        }
        catch (OperationCanceledException ex) when (!cancellationToken.IsCancellationRequested)
        {
            _logger.LogError(ex, "Timeout contacting AI CV Service [CorrelationId: {CorrelationId}]", effectiveCorrelationId);
            return ServiceResult.Failure<FastApiCvAnalysisResponseDto>(
                "AI CV service timed out.", ServiceErrorType.Infrastructure);
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "HTTP network error contacting AI CV Service [CorrelationId: {CorrelationId}]", effectiveCorrelationId);
            return ServiceResult.Failure<FastApiCvAnalysisResponseDto>(
                "Failed to reach AI CV service.", ServiceErrorType.Infrastructure);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unexpected error calling AI CV Service [CorrelationId: {CorrelationId}]", effectiveCorrelationId);
            return ServiceResult.Failure<FastApiCvAnalysisResponseDto>(
                "Unexpected error during CV analysis.", ServiceErrorType.Infrastructure);
        }
    }

    private void AttachHeaders(HttpRequestMessage request, string correlationId)
    {
        var apiKey = !string.IsNullOrWhiteSpace(_options.ApiKey)
            ? _options.ApiKey
            : _configuration["AiService:ApiKey"];

        if (!string.IsNullOrWhiteSpace(apiKey))
        {
            request.Headers.Add(InternalApiKeyHeader, apiKey);
        }

        request.Headers.Add(CorrelationIdHeader, correlationId);
    }

    private async Task<ServiceResult<FastApiCvAnalysisResponseDto>> HandleResponseAsync(
        HttpResponseMessage response,
        string endpoint,
        string correlationId,
        long durationMs,
        CancellationToken cancellationToken)
    {
        var responseBody = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            string? errorCode = null;
            if (!string.IsNullOrWhiteSpace(responseBody))
            {
                try
                {
                    using var doc = JsonDocument.Parse(responseBody);
                    if (doc.RootElement.TryGetProperty("code", out var codeProp))
                    {
                        errorCode = codeProp.GetString();
                    }
                }
                catch
                {
                    // Ignore JSON parsing issues when inspecting error code
                }
            }

            _logger.LogWarning(
                "AI CV Service returned HTTP {StatusCode}, ErrorCode={ErrorCode} in {DurationMs}ms at {Endpoint} [CorrelationId: {CorrelationId}]",
                (int)response.StatusCode,
                errorCode ?? "N/A",
                durationMs,
                endpoint,
                correlationId);

            var errorType = response.StatusCode switch
            {
                HttpStatusCode.Unauthorized => ServiceErrorType.Unauthorized,
                HttpStatusCode.Forbidden => ServiceErrorType.Forbidden,
                HttpStatusCode.BadRequest or HttpStatusCode.UnprocessableEntity or HttpStatusCode.UnsupportedMediaType => ServiceErrorType.Validation,
                HttpStatusCode.NotFound => ServiceErrorType.NotFound,
                _ => ServiceErrorType.Infrastructure
            };

            return ServiceResult.Failure<FastApiCvAnalysisResponseDto>(
                $"AI CV Service failed with HTTP {(int)response.StatusCode}", errorType);
        }

        try
        {
            var result = JsonSerializer.Deserialize<FastApiCvAnalysisResponseDto>(responseBody, _jsonOptions);
            if (result is null)
            {
                _logger.LogError(
                    "AI CV Service returned null analysis data in {DurationMs}ms at {Endpoint} [CorrelationId: {CorrelationId}]",
                    durationMs,
                    endpoint,
                    correlationId);
                return ServiceResult.Failure<FastApiCvAnalysisResponseDto>(
                    "AI CV Service returned null analysis data.", ServiceErrorType.Infrastructure);
            }

            _logger.LogInformation(
                "AI CV Service succeeded in {DurationMs}ms at {Endpoint} [CorrelationId: {CorrelationId}]",
                durationMs,
                endpoint,
                correlationId);

            return ServiceResult.Success(result);
        }
        catch (JsonException ex)
        {
            _logger.LogError(
                ex,
                "Failed to deserialize AI CV response in {DurationMs}ms at {Endpoint} [CorrelationId: {CorrelationId}]",
                durationMs,
                endpoint,
                correlationId);
            return ServiceResult.Failure<FastApiCvAnalysisResponseDto>(
                "Malformed response from AI CV Service.", ServiceErrorType.Infrastructure);
        }
    }
}
