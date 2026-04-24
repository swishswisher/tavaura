using System.Text.Json.Serialization;

namespace Tavaura.Api.Worker.Contracts;

public class WorkerIngestionMockResponse
{
    [JsonPropertyName("job_id")]
    public string JobId { get; set; } = string.Empty;

    [JsonPropertyName("pipeline")]
    public string Pipeline { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("started_at")]
    public DateTime StartedAt { get; set; }

    [JsonPropertyName("completed_at")]
    public DateTime CompletedAt { get; set; }

    [JsonPropertyName("classification_hint")]
    public string ClassificationHint { get; set; } = string.Empty;

    [JsonPropertyName("segmentation_mask_url")]
    public string SegmentationMaskUrl { get; set; } = string.Empty;

    [JsonPropertyName("canonical_asset_version")]
    public string CanonicalAssetVersion { get; set; } = string.Empty;

    [JsonPropertyName("review_required")]
    public bool ReviewRequired { get; set; }

    [JsonPropertyName("notes")]
    public List<string> Notes { get; set; } = [];
}
