namespace FutureCV.Domain.Exceptions;

/// <summary>
/// Exception thrown when a business invariant or domain rule is violated within the Domain layer.
/// Completely independent of HTTP concepts and external frameworks.
/// </summary>
public class DomainException : Exception
{
    public DomainException()
    {
    }

    public DomainException(string message) : base(message)
    {
    }

    public DomainException(string message, Exception innerException) : base(message, innerException)
    {
    }
}
