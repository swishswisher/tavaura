using System;

namespace Tavaura.Api.Domain.Entities;

public class CosmeticProduct
{
    public Guid Id { get; set; }

    public Guid TenantId { get; set; }

    public string ExternalProductId { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string Type { get; set; } = string.Empty;

    public bool IsActive { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}

