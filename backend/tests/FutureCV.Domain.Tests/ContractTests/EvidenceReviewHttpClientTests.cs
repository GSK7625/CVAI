using System.Net;
using System.Text;
using FutureCV.Infrastructure.Services;
using Microsoft.Extensions.Configuration;
using Xunit;
namespace FutureCV.Domain.Tests.ContractTests;
public class EvidenceReviewHttpClientTests
{
    private sealed class Handler(string body, HttpStatusCode status) : HttpMessageHandler
    {
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken token)
        {
            Assert.Equal("http://localhost:8001/review", request.RequestUri!.ToString());
            Assert.Equal(new string('k', 32), request.Headers.GetValues("X-Internal-API-Key").Single());
            Assert.Contains("cv_text", await request.Content!.ReadAsStringAsync(token));
            return new(status) { Content = new StringContent(body, Encoding.UTF8, "application/json") };
        }
    }
    private sealed class PdfHandler : HttpMessageHandler
    {
        public int Calls;
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken token)
        {
            Calls++;
            if (request.RequestUri!.Host is "res.cloudinary.com" or "api.cloudinary.com")
            {
                Assert.False(request.Headers.Contains("X-Internal-API-Key"));
                return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK) { Content = new ByteArrayContent("%PDF-test"u8.ToArray()) });
            }
            Assert.EndsWith("/extract-pdf", request.RequestUri!.ToString());
            Assert.True(request.Headers.Contains("X-Internal-API-Key"));
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{\"text\":\"Original PDF text\"}") });
        }
    }
    [Fact]
    public async Task PdfDownload_AllowsOnlyStorageHostAndDoesNotLeakModelKey()
    {
        var config = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string,string?> { ["EvidenceAi:ApiKey"]=new string('k',32) }).Build();
        var handler = new PdfHandler();
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://localhost:8001/") };
        var client = new EvidenceReviewHttpClient(http, config);
        var denied = await client.ExtractPdfFromUrlAsync("http://127.0.0.1/private", default);
        Assert.False(denied.IsSuccess);
        Assert.Equal(0, handler.Calls);
        var result = await client.ExtractPdfFromUrlAsync("https://res.cloudinary.com/test/raw/upload/cv.pdf", default);
        Assert.True(result.IsSuccess);
        Assert.Equal("Original PDF text", result.Data);
        Assert.Equal(2, handler.Calls);
    }

    [Fact]
    public async Task PdfDownload_SignsStoredCvWithoutSendingInternalKeyToCloudinary()
    {
        var config = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string,string?> {
            ["EvidenceAi:ApiKey"]=new string('k',32), ["Cloudinary:CloudName"]="test", ["Cloudinary:ApiKey"]="fixture",
            ["Cloudinary:ApiSecret"]="fixture-secret" }).Build();
        var handler = new PdfHandler();
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://localhost:8001/") };
        var result = await new EvidenceReviewHttpClient(http, config).ExtractPdfFromUrlAsync(
            "https://res.cloudinary.com/test/raw/upload/cv.pdf", default, "cvs/candidates/cv.pdf");
        Assert.True(result.IsSuccess);
        Assert.Equal(2, handler.Calls);
    }

    [Theory]
    [InlineData("ready", "87.5", true)]
    [InlineData("needs_review", "null", true)]
    [InlineData("ready", "null", false)]
    [InlineData("ready", "101", false)]
    [InlineData("needs_review", "0", false)]
    public async Task EnforcesNullableScoreContract(string status, string score, bool success)
    {
        var config = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string,string?> {
            ["EvidenceAi:Enabled"]="true", ["EvidenceAi:ApiKey"]=new string('k',32) }).Build();
        using var http = new HttpClient(new Handler($"{{\"status\":\"{status}\",\"score\":{score},\"assessments\":[]}}", HttpStatusCode.OK)) {
            BaseAddress = new Uri("http://localhost:8001/") };
        var result = await new EvidenceReviewHttpClient(http, config).ReviewAsync("original CV", "Basic Python", "Backend", default);
        Assert.Equal(success, result.IsSuccess);
    }
}
