namespace Tavaura.Api.Models.Jobs;

public class RenderResultListItemResponse
{
    public Guid RenderJobId { get; set; }

    public Guid? RenderResultId { get; set; }

    public string GarmentName { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public string? ErrorMessage { get; set; }

    public string? OutputImageUrl { get; set; }

    public string? PreviewImageUrl { get; set; }

    public DateTime CreatedAt { get; set; }
}
