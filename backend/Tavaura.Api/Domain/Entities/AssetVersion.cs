using System;

namespace Tavaura.Api.Domain.Entities;

public class AssetVersion
{
    public Guid Id { get; set; }

    public Guid TenantId { get; set; }

    public Guid GarmentAssetId { get; set; }

    public int VersionNumber { get; set; }

    public string ProcessingModel { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }
}
