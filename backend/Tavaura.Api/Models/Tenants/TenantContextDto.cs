using System;

namespace Tavaura.Api.Models.Tenants;

public class TenantContextDto
{
    public Guid? TenantId { get; set; }

    public string? Platform { get; set; }

    public string? Domain { get; set; }

    public bool HasTenant { get; set; }
}

