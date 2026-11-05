using FutureCV.Application.Features.Job.DTOs;
using FutureCV.Application.Features.Job.Validators;
using Xunit;
namespace FutureCV.Domain.Tests.ContractTests;
public class JobDeadlineTests
{
    [Fact]
    public void CreateAndUpdate_RejectMissingTimezoneButAcceptUtc()
    {
        var utc = DateTime.UtcNow.AddDays(5);
        var naive = DateTime.SpecifyKind(utc, DateTimeKind.Unspecified);
        CreateJobRequest Create(DateTime time) => new("Fixture", "Description", null, null, null, null, null, null, null, null, Deadline: time);
        UpdateJobRequest Update(DateTime time) => new("Fixture", "Description", null, null, null, null, null, null, null, null, Deadline: time);
        var create = new CreateJobValidator();
        var update = new UpdateJobValidator();
        Assert.False(create.Validate(Create(naive)).IsValid);
        Assert.False(update.Validate(Update(naive)).IsValid);
        Assert.True(create.Validate(Create(utc)).IsValid);
        Assert.True(update.Validate(Update(utc)).IsValid);
    }
}
