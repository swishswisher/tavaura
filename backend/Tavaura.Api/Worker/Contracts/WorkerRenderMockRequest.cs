namespace Tavaura.Api.Worker.Contracts;

public class WorkerRenderMockRequest
{
    public string JobId { get; set; } = string.Empty;

    public string TenantId { get; set; } = string.Empty;

    public string Mode { get; set; } = "avatar";

    public string? AvatarId { get; set; }

    public string? PhotoInputUrl { get; set; }

    public string GarmentAssetId { get; set; } = string.Empty;

    public string AssetVersionId { get; set; } = string.Empty;
}

