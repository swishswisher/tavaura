using System;

namespace Tavaura.Api.Domain.Entities;

public class IngestionJob
{
    public Guid Id { get; set; }

    public Guid TenantId { get; set; }

    public string ExternalProductId { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public int AttemptCount { get; set; }

    public string? ErrorMessage { get; set; }

    public DateTime? StartedAt { get; set; }

    public DateTime? CompletedAt { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}
