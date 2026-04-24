namespace Tavaura.Api.Models.Jobs;

public class RenderJobResponse
{
    public Guid Id { get; set; }

    public Guid TenantId { get; set; }

    public Guid AvatarId { get; set; }

    public Guid GarmentId { get; set; }

    public Guid GarmentAssetId { get; set; }

    public Guid AssetVersionId { get; set; }

    public string Status { get; set; } = string.Empty;

    public int AttemptCount { get; set; }

    public string? ErrorMessage { get; set; }

    public DateTime? StartedAt { get; set; }

    public DateTime? CompletedAt { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}

