namespace Tavaura.Api.Configuration;

public class WorkerOptions
{
    public const string SectionName = "Worker";

    public string BaseUrl { get; set; } = "http://localhost:8001";
}

