namespace Tavaura.Api.Worker.Contracts;

public class WorkerRenderMockResponse
{
    public string JobId { get; set; } = string.Empty;

    public string Pipeline { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public DateTime StartedAt { get; set; }

    public DateTime CompletedAt { get; set; }

    public string RenderOutputUrl { get; set; } = string.Empty;

    public string PreviewOutputUrl { get; set; } = string.Empty;

    public List<string> Notes { get; set; } = [];
}

