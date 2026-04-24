using System.ComponentModel.DataAnnotations;

namespace Tavaura.Api.Models.Render;

public class MockRunRenderRequest
{
    [Required]
    public Guid TenantId { get; set; }

    [Required]
    public Guid AvatarId { get; set; }

    [Required]
    public Guid GarmentAssetId { get; set; }

    [Required]
    public Guid AssetVersionId { get; set; }

    public string Mode { get; set; } = "avatar";

    public string? PhotoInputUrl { get; set; }
}

