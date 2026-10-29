using System.Net;
using System.Text;
using FutureCV.Application.Common.Models;
using FutureCV.Infrastructure.Configurations;
using FutureCV.Infrastructure.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Options;
using Xunit;

namespace FutureCV.Domain.Tests.ContractTests;

public class AiCvHttpClientTests
{
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

    private static AiCvHttpClient CreateClient(
        HttpMessageHandler handler,
        AiServiceOptions? options = null,
        TestLogger<AiCvHttpClient>? logger = null)
    {
        var httpClient = new HttpClient(handler)
        {
            BaseAddress = new Uri("http://localhost:8000/")
        };

        var config = new ConfigurationBuilder().Build();
        var testLogger = logger ?? new TestLogger<AiCvHttpClient>();
        var opts = Options.Create(options ?? new AiServiceOptions());

        return new AiCvHttpClient(httpClient, config, testLogger, opts);
    }

    [Fact]
    public async Task AnalyzeTextAsync_SendsCorrectHeaders_ApiKeyAndCorrelationId()
    {
        HttpRequestMessage? capturedRequest = null;
        var validResponse = """
        {
            "structured_cv": null,
            "cv_score": 85,
            "strengths": ["Strong skills"],
            "weaknesses": [],
            "improvement_suggestions": [],
            "raw_text": "Sample text"
        }
        """;

        var handler = new DelegatingMockHandler((req, _) =>
        {
            capturedRequest = req;
            var resp = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(validResponse, Encoding.UTF8, "application/json")
            };
            return Task.FromResult(resp);
        });

        var options = new AiServiceOptions
        {
            ApiKey = "futurecv-demo-local-2026"
        };
        var client = CreateClient(handler, options);
        var result = await client.AnalyzeTextAsync("My CV raw text", candidateId: "cand-1", correlationId: "corr-ai-cv-1");

        Assert.True(result.IsSuccess);
        Assert.NotNull(capturedRequest);
        Assert.True(capturedRequest.Headers.Contains("X-Internal-API-Key"));
        Assert.Equal("futurecv-demo-local-2026", capturedRequest.Headers.GetValues("X-Internal-API-Key").First());
        Assert.True(capturedRequest.Headers.Contains("X-Correlation-ID"));
        Assert.Equal("corr-ai-cv-1", capturedRequest.Headers.GetValues("X-Correlation-ID").First());
    }

    [Fact]
    public async Task AnalyzeTextAsync_WithUnauthorized_ReturnsUnauthorized()
    {
        var handler = new DelegatingMockHandler((_, _) =>
        {
            var resp = new HttpResponseMessage(HttpStatusCode.Unauthorized);
            return Task.FromResult(resp);
        });

        var client = CreateClient(handler);
        var result = await client.AnalyzeTextAsync("Text content");

        Assert.False(result.IsSuccess);
        Assert.Equal(ServiceErrorType.Unauthorized, result.ErrorType);
    }

    [Fact]
    public async Task AnalyzeTextAsync_OnError_DoesNotLogResponseBodyOrPii()
    {
        var testLogger = new TestLogger<AiCvHttpClient>();
        var sensitivePiiBody = """
        {
            "code": "PROVIDER_ERROR",
            "message": "Model generation failed",
            "sensitive_candidate_data": "SECRET_SALARY_60000000_VND"
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

        var client = CreateClient(handler, logger: testLogger);
        var result = await client.AnalyzeTextAsync("CV raw text");

        Assert.False(result.IsSuccess);
        Assert.Equal(ServiceErrorType.Infrastructure, result.ErrorType);

        // Verify PII is NOT in any log message
        foreach (var msg in testLogger.LoggedMessages)
        {
            Assert.DoesNotContain("SECRET_SALARY_60000000_VND", msg);
        }

        // Verify status code and error code are logged
        var warningMsg = testLogger.LoggedMessages.FirstOrDefault(m => m.Contains("ErrorCode=PROVIDER_ERROR"));
        Assert.NotNull(warningMsg);
        Assert.Contains("503", warningMsg);
    }

    [Fact]
    public async Task AnalyzeTextAsync_WithMalformedJson_DoesNotLogRawJsonBody()
    {
        var testLogger = new TestLogger<AiCvHttpClient>();
        var brokenJsonWithPii = "{ invalid json containing candidate email secret@personal.com";

        var handler = new DelegatingMockHandler((_, _) =>
        {
            var resp = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(brokenJsonWithPii, Encoding.UTF8, "application/json")
            };
            return Task.FromResult(resp);
        });

        var client = CreateClient(handler, logger: testLogger);
        var result = await client.AnalyzeTextAsync("CV raw text");

        Assert.False(result.IsSuccess);
        Assert.Equal(ServiceErrorType.Infrastructure, result.ErrorType);

        // Verify the raw broken JSON is NOT printed in the error log
        foreach (var msg in testLogger.LoggedMessages)
        {
            Assert.DoesNotContain("secret@personal.com", msg);
        }
    }
}

