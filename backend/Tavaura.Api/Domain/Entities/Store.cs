using System;

namespace Tavaura.Api.Domain.Entities;

public class Store
{
    public Guid Id { get; set; }

    public Guid AccountId { get; set; }

    public Guid TenantId { get; set; }

    public string Name { get; set; } = string.Empty;

    public string Slug { get; set; } = string.Empty;

    public string Platform { get; set; } = string.Empty;

    public string? Domain { get; set; }

    public string Status { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}
