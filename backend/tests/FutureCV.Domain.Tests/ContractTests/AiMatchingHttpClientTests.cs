using System.Net;
using System.Text;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.AiMatching.DTOs;
using FutureCV.Infrastructure.Configurations;
using FutureCV.Infrastructure.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using Xunit;

namespace FutureCV.Domain.Tests.ContractTests;

public class AiMatchingHttpClientTests
{
    private static readonly AiMatchRequest DummyRequest = new(
        Cv: new AiStructuredCvDto(FullName: "Test Candidate"),
        Job: new AiStructuredJobDto(Title: "Test Job")
    );

    private static AiMatchingHttpClient CreateClient(HttpMessageHandler handler, AiServiceOptions? options = null)
    {
        var httpClient = new HttpClient(handler)
        {
            BaseAddress = new Uri("http://localhost:8000/")
        };

        var config = new ConfigurationBuilder().Build();
        var logger = NullLogger<AiMatchingHttpClient>.Instance;
        var opts = Options.Create(options ?? new AiServiceOptions());

        return new AiMatchingHttpClient(httpClient, config, logger, opts);
    }

    private sealed class DelegatingMockHandler : HttpMessageHandler
    {
        private readonly Func<HttpRequestMessage, CancellationToken, Task<HttpResponseMessage>> _handler;

        public DelegatingMockHandler(Func<HttpRequestMessage, CancellationToken, Task<HttpResponseMessage>> handler)
        {
            _handler = handler;
        }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            return _handler(request, cancellationToken);
        }
    }

    [Fact]
    public async Task MatchAsync_WithValidResponse_ReturnsSuccess()
    {
        var json = """
        {
            "match_score": 85,
            "matched_skills": ["C#", ".NET"],
            "missing_skills": ["Docker"],
            "experience_comparison": "Phù hợp",
            "education_comparison": "Đạt yêu cầu",
            "project_domain_relevance": "Tốt",
            "match_explanation": "Ứng viên rất phù hợp.",
            "meta": {
                "algorithm_version": "1.0.0",
                "contract_version": "match-result-v1",
                "llm_invoked": true,
                "explanation_mode": "llm",
                "processing_time_ms": 120.5,
                "correlation_id": "test-corr-1"
            }
        }
        """;

        var handler = new DelegatingMockHandler((_, _) =>
        {
            var resp = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(json, Encoding.UTF8, "application/json")
            };
            return Task.FromResult(resp);
        });

        var client = CreateClient(handler);
        var result = await client.MatchAsync(DummyRequest);

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Data);
        Assert.Equal(85, result.Data.MatchScore);
        Assert.Equal(2, result.Data.MatchedSkills.Count);
        Assert.Single(result.Data.MissingSkills);
        Assert.Equal("match-result-v1", result.Data.Meta.ContractVersion);
    }

    [Theory]
    [InlineData(101)]
    [InlineData(150)]
    [InlineData(200)]
    [InlineData(-1)]
    [InlineData(-50)]
    public async Task MatchAsync_WithOutOfBoundsScore_RejectsWithInfrastructureError(int invalidScore)
    {
        var json = $$"""
        {
            "match_score": {{invalidScore}},
            "matched_skills": [],
            "missing_skills": [],
            "experience_comparison": "",
            "education_comparison": "",
            "project_domain_relevance": ""
        }
        """;

        var handler = new DelegatingMockHandler((_, _) =>
        {
            var resp = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(json, Encoding.UTF8, "application/json")
            };
            return Task.FromResult(resp);
        });

        var client = CreateClient(handler);
        var result = await client.MatchAsync(DummyRequest);

        Assert.False(result.IsSuccess);
        Assert.Equal(ServiceErrorType.Infrastructure, result.ErrorType);
        Assert.Contains("invalid match score", result.ErrorMessage, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task MatchAsync_WithEmptyBody_ReturnsInfrastructureError()
    {
        var handler = new DelegatingMockHandler((_, _) =>
        {
            var resp = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent("", Encoding.UTF8, "application/json")
            };
            return Task.FromResult(resp);
        });

        var client = CreateClient(handler);
        var result = await client.MatchAsync(DummyRequest);

        Assert.False(result.IsSuccess);
        Assert.Equal(ServiceErrorType.Infrastructure, result.ErrorType);
        Assert.Contains("empty", result.ErrorMessage, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task MatchAsync_WithMalformedJson_ReturnsInfrastructureError()
    {
        var handler = new DelegatingMockHandler((_, _) =>
        {
            var resp = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent("{ not valid json at all ...", Encoding.UTF8, "application/json")
            };
            return Task.FromResult(resp);
        });

        var client = CreateClient(handler);
        var result = await client.MatchAsync(DummyRequest);

        Assert.False(result.IsSuccess);
        Assert.Equal(ServiceErrorType.Infrastructure, result.ErrorType);
        Assert.Contains("parse", result.ErrorMessage, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task MatchAsync_WithUnauthorizedStatus_ReturnsUnauthorizedError()
    {
        var handler = new DelegatingMockHandler((_, _) =>
        {
            var resp = new HttpResponseMessage(HttpStatusCode.Unauthorized);
            return Task.FromResult(resp);
        });

        var client = CreateClient(handler);
        var result = await client.MatchAsync(DummyRequest);

        Assert.False(result.IsSuccess);
        Assert.Equal(ServiceErrorType.Unauthorized, result.ErrorType);
    }

    [Fact]
    public async Task MatchAsync_SendsCorrectHeaders_ApiKeyAndCorrelationId()
    {
        HttpRequestMessage? capturedRequest = null;
        var handler = new DelegatingMockHandler((req, _) =>
        {
            capturedRequest = req;
            var json = """
            {
                "match_score": 80,
                "matched_skills": [],
                "missing_skills": [],
                "experience_comparison": "",
                "education_comparison": "",
                "project_domain_relevance": ""
            }
            """;
            var resp = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(json, Encoding.UTF8, "application/json")
            };
            return Task.FromResult(resp);
        });

        var options = new AiServiceOptions
        {
            ApiKey = "futurecv-demo-local-2026"
        };
        var client = CreateClient(handler, options);
        var result = await client.MatchAsync(DummyRequest, correlationId: "custom-corr-123");

        Assert.True(result.IsSuccess);
        Assert.NotNull(capturedRequest);
        Assert.True(capturedRequest.Headers.Contains("X-Internal-API-Key"));
        Assert.Equal("futurecv-demo-local-2026", capturedRequest.Headers.GetValues("X-Internal-API-Key").First());
        Assert.True(capturedRequest.Headers.Contains("X-Correlation-ID"));
        Assert.Equal("custom-corr-123", capturedRequest.Headers.GetValues("X-Correlation-ID").First());
    }

    [Fact]
    public async Task MatchAsync_OnError_DoesNotLogResponseBodyOrPii()
    {
        var testLogger = new TestLogger<AiMatchingHttpClient>();
        var sensitivePiiBody = """
        {
            "code": "PROVIDER_ERROR",
            "message": "Model failed",
            "candidate_pii_phone": "+84999999999",
            "sensitive_secret_text": "TOP_SECRET_SALARY_999999"
        }
        """;

        var handler = new DelegatingMockHandler((_, _) =>
        {
            var resp = new HttpResponseMessage(HttpStatusCode.ServiceUnavailable)
            {
                Content = new StringContent(sensitivePiiBody, Encoding.UTF8, "application/json")
            };
            return Task.FromResult(resp);
        });

        var httpClient = new HttpClient(handler)
        {
            BaseAddress = new Uri("http://localhost:8000/")
        };
        var config = new ConfigurationBuilder().Build();
        var client = new AiMatchingHttpClient(httpClient, config, testLogger, Options.Create(new AiServiceOptions()));

        var result = await client.MatchAsync(DummyRequest);

        Assert.False(result.IsSuccess);
        Assert.Equal(ServiceErrorType.Infrastructure, result.ErrorType);

        // Assert: NO logs contain the sensitive response body or PII
        foreach (var log in testLogger.LoggedMessages)
        {
            Assert.DoesNotContain("TOP_SECRET_SALARY_999999", log);
            Assert.DoesNotContain("+84999999999", log);
        }
        // Assert: Log contains StatusCode and ErrorCode
        var warningLog = testLogger.LoggedMessages.FirstOrDefault(m => m.Contains("ErrorCode=PROVIDER_ERROR"));
        Assert.NotNull(warningLog);
        Assert.Contains("503", warningLog);
    }

    private sealed class TestLogger<T> : Microsoft.Extensions.Logging.ILogger<T>
    {
        public List<string> LoggedMessages { get; } = new();

        public IDisposable? BeginScope<TState>(TState state) where TState : notnull => null;
        public bool IsEnabled(Microsoft.Extensions.Logging.LogLevel logLevel) => true;

        public void Log<TState>(
            Microsoft.Extensions.Logging.LogLevel logLevel,
            Microsoft.Extensions.Logging.EventId eventId,
            TState state,
            Exception? exception,
            Func<TState, Exception?, string> formatter)
        {
            LoggedMessages.Add(formatter(state, exception));
        }
    }
}

