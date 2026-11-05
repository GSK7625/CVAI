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
