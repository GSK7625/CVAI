using FutureCV.Infrastructure.Configurations;
using FutureCV.Infrastructure.Services;
using Microsoft.Extensions.Options;
using Xunit;

namespace FutureCV.Domain.Tests.ContractTests;

public class CloudinaryPreviewTests
{
    private static CloudinaryFileStorage Storage() => new(Options.Create(new CloudinarySettings
        { CloudName = "fixture", ApiKey = "test-key", ApiSecret = "test-secret" }));

    [Fact]
    public void Preview_IsSignedInlineAndExpiresSoon()
    {
        var before = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        var url = new Uri(Storage().GetDocumentPreviewUrl("cvs/candidates/cv intern.pdf"));
        Assert.Equal("https", url.Scheme);
        Assert.Equal("api.cloudinary.com", url.Host);
        Assert.Equal("/v1_1/fixture/raw/download", url.AbsolutePath);
        var query = url.Query.TrimStart('?').Split('&').Select(x => x.Split('=', 2))
            .ToDictionary(x => x[0], x => Uri.UnescapeDataString(x[1].Replace('+', ' ')));
        Assert.Equal("cvs/candidates/cv intern.pdf", query["public_id"]);
        Assert.Equal("upload", query["type"]);
        Assert.Equal("false", query["attachment"]);
        Assert.InRange(long.Parse(query["expires_at"]), before + 119, before + 125);
        Assert.NotEmpty(query["signature"]);
        Assert.DoesNotContain("test-secret", url.ToString());
    }

    [Theory]
    [InlineData("avatars/candidate.pdf")]
    [InlineData("cvs/candidates/payload.html")]
    [InlineData("")]
    public void Preview_RejectsNonCvAssets(string id) =>
        Assert.Throws<ArgumentException>(() => Storage().GetDocumentPreviewUrl(id));
}
