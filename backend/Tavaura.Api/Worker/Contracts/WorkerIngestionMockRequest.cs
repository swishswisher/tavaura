using System.Text.Json.Serialization;

namespace Tavaura.Api.Worker.Contracts;

public class WorkerIngestionMockRequest
{
    [JsonPropertyName("job_id")]
    public string JobId { get; set; } = string.Empty;

    [JsonPropertyName("tenant_id")]
    public string TenantId { get; set; } = string.Empty;

    [JsonPropertyName("garment_id")]
    public string GarmentId { get; set; } = string.Empty;

    [JsonPropertyName("source_type")]
    public string SourceType { get; set; } = "catalog_import";

    [JsonPropertyName("source_image_urls")]
    public List<string> SourceImageUrls { get; set; } = [];

    [JsonPropertyName("external_product_id")]
    public string? ExternalProductId { get; set; }
}
