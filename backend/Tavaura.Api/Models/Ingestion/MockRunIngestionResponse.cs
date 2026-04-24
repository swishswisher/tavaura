namespace Tavaura.Api.Models.Ingestion;

public class MockRunIngestionResponse
{
    public Guid IngestionJobId { get; set; }

    public string Status { get; set; } = string.Empty;

    public DateTime StartedAt { get; set; }

    public DateTime CompletedAt { get; set; }

    public string ClassificationHint { get; set; } = string.Empty;

    public string SegmentationMaskUrl { get; set; } = string.Empty;

    public string CanonicalAssetVersion { get; set; } = string.Empty;

    public bool ReviewRequired { get; set; }
}

