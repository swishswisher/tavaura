using System.Net;

namespace Tavaura.Api.Worker;

public class WorkerClientException : Exception
{
    public WorkerClientException(string message, HttpStatusCode? statusCode = null, Exception? innerException = null)
        : base(message, innerException)
    {
        StatusCode = statusCode;
    }

    public HttpStatusCode? StatusCode { get; }
}

