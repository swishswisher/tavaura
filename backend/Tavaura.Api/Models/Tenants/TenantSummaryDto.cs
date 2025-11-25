using System;

namespace Tavaura.Api.Models.Tenants;

public class TenantSummaryDto
{
    public Guid Id { get; set; }

    public string Name { get; set; } = string.Empty;

    public string? Domain { get; set; }

    public string Platform { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public string Plan { get; set; } = string.Empty;
}

