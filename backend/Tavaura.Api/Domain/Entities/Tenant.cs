using System;

namespace Tavaura.Api.Domain.Entities;

/// <summary>
/// Represents a merchant or brand tenant that operates a storefront within the Tavaura platform.
/// Tracks identity, hosting platform, billing status, and timestamps for lifecycle monitoring.
/// </summary>
public class Tenant
{
    public Guid Id { get; set; }

    public string Name { get; set; } = string.Empty;

    public string? Domain { get; set; }

    public string Platform { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public string Plan { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}

