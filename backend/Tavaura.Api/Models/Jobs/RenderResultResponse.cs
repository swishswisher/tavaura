namespace Tavaura.Api.Models.Jobs;

public class RenderResultResponse
{
    public Guid RenderJobId { get; set; }

    public string Status { get; set; } = string.Empty;

    public string? ErrorMessage { get; set; }

    public DateTime? StartedAt { get; set; }

    public DateTime? CompletedAt { get; set; }

    public Guid RenderResultId { get; set; }

    public string OutputImageUrl { get; set; } = string.Empty;

    public string PreviewImageUrl { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }
}

