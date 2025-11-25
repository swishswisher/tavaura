using System;

namespace Tavaura.Api.Domain.Entities;

public class Challenge
{
    public Guid Id { get; set; }

    public Guid TenantId { get; set; }

    public string Slug { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string Description { get; set; } = string.Empty;

    public DateTime StartsAt { get; set; }

    public DateTime EndsAt { get; set; }

    public bool IsActive { get; set; }
}

