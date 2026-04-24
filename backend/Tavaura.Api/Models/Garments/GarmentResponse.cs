namespace Tavaura.Api.Models.Garments;

public class GarmentResponse
{
    public Guid Id { get; set; }

    public Guid TenantId { get; set; }

    public string ExternalProductId { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string Category { get; set; } = string.Empty;

    public string Layer { get; set; } = string.Empty;

    public string SourceImageUrl { get; set; } = string.Empty;

    public bool IsActive { get; set; }

    public string Status { get; set; } = string.Empty;

    public bool HasProcessedAsset { get; set; }

    public string? ProcessedImageUrl { get; set; }

    public string? ProcessedMaskUrl { get; set; }

    public string? ProcessedTextureUrl { get; set; }

    public DateTime? LatestAssetCreatedAt { get; set; }

    public string? LatestIngestionStatus { get; set; }

    public string? LatestIngestionErrorMessage { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}
