using System.Net;
using System.Net.Mail;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Infrastructure.Identity;
using Microsoft.Extensions.Options;

namespace FutureCV.Infrastructure.Services;

public class EmailService : IEmailService
{
    private readonly SmtpSettings _settings;

    public EmailService(IOptions<SmtpSettings> settings)
    {
        _settings = settings.Value;
    }

    public async Task SendEmailAsync(
        string toEmail,
        string subject,
        string bodyHtml,
        CancellationToken cancellationToken = default)
    {
        using var message = new MailMessage();
        message.From = new MailAddress(_settings.SenderEmail, _settings.SenderName);
        message.To.Add(new MailAddress(toEmail));
        message.Subject = subject;
        message.Body = bodyHtml;
        message.IsBodyHtml = true;

        using var client = new SmtpClient(_settings.Host, _settings.Port);
        client.Credentials = new NetworkCredential(_settings.Username, _settings.Password);
        client.EnableSsl = _settings.EnableSsl;

        await client.SendMailAsync(message, cancellationToken);
    }
}
