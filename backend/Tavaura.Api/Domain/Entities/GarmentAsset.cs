using System;

namespace Tavaura.Api.Domain.Entities;

public class GarmentAsset
{
    public Guid Id { get; set; }

    public Guid TenantId { get; set; }

    public Guid GarmentId { get; set; }

    public string AssetType { get; set; } = string.Empty;

    public string SourceImageUrl { get; set; } = string.Empty;

    public string? ProcessedImageUrl { get; set; }

    public string? ProcessedMaskUrl { get; set; }

    public string? ProcessedTextureUrl { get; set; }

    public float ConfidenceScore { get; set; }

    public DateTime CreatedAt { get; set; }
}
