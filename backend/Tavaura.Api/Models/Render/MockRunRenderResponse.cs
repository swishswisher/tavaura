namespace Tavaura.Api.Models.Render;

public class MockRunRenderResponse
{
    public Guid RenderJobId { get; set; }

    public Guid RenderResultId { get; set; }

    public string Status { get; set; } = string.Empty;

    public DateTime StartedAt { get; set; }

    public DateTime CompletedAt { get; set; }

    public string OutputImageUrl { get; set; } = string.Empty;

    public string PreviewImageUrl { get; set; } = string.Empty;
}

