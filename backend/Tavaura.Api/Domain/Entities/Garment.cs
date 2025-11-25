using System;

namespace Tavaura.Api.Domain.Entities;

public class Garment
{
    public Guid Id { get; set; }

    public Guid TenantId { get; set; }

    public string ExternalProductId { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string Category { get; set; } = string.Empty;

    public string Layer { get; set; } = string.Empty;

    public string SourceImageUrl { get; set; } = string.Empty;

    public string? ProcessedModelUrl { get; set; }

    public bool IsActive { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}

